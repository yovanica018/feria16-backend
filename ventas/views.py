from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status
from django.utils import timezone
from datetime import timedelta

from django.contrib.gis.geos import Point

from ventas.models import ARTICULOS_VENTA
from usuarios.models import UBICACIONES

from django.db.models import Count, Q, OuterRef, Subquery
from interacciones.models import CALIFICACIONES

class ComerciantesPorArticuloAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):

        # ==========================================
        # 🔎 OBTENER PARÁMETROS
        # ==========================================
        id_articulo = request.GET.get("id_articulo")
        latitude = request.GET.get("latitude")
        longitude = request.GET.get("longitude")

        # validar artículo obligatorio
        if not id_articulo:
            return Response(
                {"error": "Falta parámetro id_articulo"},
                status=400
            )

        # ==========================================
        # 📍 VALIDAR COORDENADAS DEL VISITANTE
        # ==========================================
        try:
            latitude = float(latitude) if latitude is not None else 0
            longitude = float(longitude) if longitude is not None else 0
        except (ValueError, TypeError):
            return Response(
                {"error": "Latitud o longitud inválidas"},
                status=400
            )

        # determinar si se calculará distancia
        usar_distancia = not (latitude == 0 and longitude == 0)

        user_point = None
        if usar_distancia:
            user_point = Point(longitude, latitude, srid=4326)

        # ==========================================
        # 🕒 FECHA BASE PARA ACTIVIDAD
        # ==========================================
        hace_30_dias = timezone.now() - timedelta(days=30)

        # ==========================================
        # 📍 SUBQUERY ÚLTIMA UBICACIÓN
        # evita consultar ubicación dentro del for
        # ==========================================
        ultima_ubicacion = (
            UBICACIONES.objects
            .filter(id_user=OuterRef("id_user"))
            .order_by("-fecha_actualizacion")
        )

        # ==========================================
        # 🔍 CONSULTA PRINCIPAL OPTIMIZADA
        # ==========================================
        publicaciones = (
            ARTICULOS_VENTA.objects
            .filter(
                id_articulo_id=id_articulo,
                estado="activo",
                id_user__rol="comerciante",
                id_user__estado="activo",
                id_user__suscripciones__estado="vigente"
            )
            .select_related(
                "id_user",
                "id_user__negocio",
                "id_articulo"
            )
            .annotate(
                # ==========================================
                # ⭐ CALIFICACIONES
                # ==========================================
                total_positivos=Count(
                    "id_user__calificaciones_recibidas",
                    filter=Q(
                        id_user__calificaciones_recibidas__tipo_calificacion="positivo"
                    ),
                    distinct=True
                ),

                total_negativos=Count(
                    "id_user__calificaciones_recibidas",
                    filter=Q(
                        id_user__calificaciones_recibidas__tipo_calificacion="negativo"
                    ),
                    distinct=True
                ),

                # ==========================================
                # 🔥 ACTIVIDAD ÚLTIMOS 30 DÍAS
                # ==========================================
                actividad_count=Count(
                    "id_user__articulos_venta",
                    filter=Q(
                        id_user__articulos_venta__estado="activo",
                        id_user__articulos_venta__fecha__gte=hace_30_dias
                    ),
                    distinct=True
                ),

                # ==========================================
                # 📍 ÚLTIMA UBICACIÓN
                # ==========================================
                latitud_actual=Subquery(
                    ultima_ubicacion.values("latitud")[:1]
                ),

                longitud_actual=Subquery(
                    ultima_ubicacion.values("longitud")[:1]
                ),

                geometria_actual=Subquery(
                    ultima_ubicacion.values("geometria_user")[:1]
                )
            )
            .order_by("-fecha")
        )

        resultado = []

        # ==========================================
        # 🔄 PROCESAR RESULTADO FINAL
        # ==========================================
        for venta in publicaciones:

            usuario = venta.id_user
            negocio = getattr(usuario, "negocio", None)

            # ==========================================
            # 📍 DISTANCIA
            # ==========================================
            distancia = None

            if usar_distancia and venta.geometria_actual:
                distancia = round(
                    venta.geometria_actual.distance(user_point) * 111000,
                    2
                )

            # ==========================================
            # ⭐ SCORE REPUTACIÓN
            # ==========================================
            total_positivos = venta.total_positivos
            total_negativos = venta.total_negativos

            total_calificaciones = (
                total_positivos + total_negativos
            )

            score_recomendacion = (
                round(
                    (total_positivos / total_calificaciones) * 100,
                    1
                )
                if total_calificaciones > 0
                else 0
            )

            # ==========================================
            # 🔥 SCORE ACTIVIDAD
            # peso máximo: 15 puntos
            # ==========================================
            actividad_score = min(
                venta.actividad_count * 3,
                15
            )

            # ==========================================
            # 📍 SCORE DISTANCIA
            # peso máximo: 50 puntos
            # ==========================================
            if distancia is None:
                distancia_score = 0
            elif distancia <= 50:
                distancia_score = 50
            elif distancia <= 100:
                distancia_score = 45
            elif distancia <= 200:
                distancia_score = 40
            elif distancia <= 300:
                distancia_score = 35
            elif distancia <= 500:
                distancia_score = 25
            else:
                distancia_score = 15

            # ==========================================
            # ⭐ SCORE REPUTACIÓN
            # peso máximo: 35 puntos
            # ==========================================
            reputacion_score = round(
                score_recomendacion * 0.35,
                2
            )

            # ==========================================
            # 🏆 RANKING FINAL
            # ==========================================
            ranking_total = round(
                distancia_score +
                reputacion_score +
                actividad_score,
                2
            )

            resultado.append({
                "id_venta": venta.id_venta,
                "id_user": usuario.id_user,
                "nombre_usuario": usuario.nombre,
                "nombre_negocio": negocio.nombre_negocio if negocio else "",
                "descripcion_negocio": negocio.descripcion if negocio else "",
                "descripcion_publicacion": venta.descripcion,
                "precio": str(venta.precio),
                "fecha": venta.fecha,

                "latitud": float(venta.latitud_actual) if venta.latitud_actual else None,
                "longitud": float(venta.longitud_actual) if venta.longitud_actual else None,
                "distancia_m": distancia,

                # reputación
                "total_positivos": total_positivos,
                "total_negativos": total_negativos,
                "score_recomendacion": score_recomendacion,

                # ranking
                "ranking_score": ranking_total,
                "actividad_score": actividad_score,
                "distancia_score": distancia_score,
                "reputacion_score": reputacion_score,
            })

        # ==========================================
        # 🏆 ORDENAR POR SCORE DESCENDENTE, MENOR DISTANCIA Y MAS ACTIVO
        # ==========================================
        resultado.sort(
            key=lambda x: (
                -x["ranking_score"],
                x["distancia_m"] if x["distancia_m"] is not None else 999999,
                -x["actividad_score"]
            )
        )

        return Response({
            "count": len(resultado),
            "results": resultado
        })

class TiendasPorArticuloAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):

        # ==========================================
        # 🔎 OBTENER PARÁMETROS
        # ==========================================
        id_articulo = request.GET.get("id_articulo")
        latitude = request.GET.get("latitude")
        longitude = request.GET.get("longitude")

        # validar artículo obligatorio
        if not id_articulo:
            return Response(
                {"error": "Falta parámetro id_articulo"},
                status=400
            )

        # ==========================================
        # 📍 VALIDAR COORDENADAS DEL VISITANTE
        # ==========================================
        try:
            latitude = float(latitude) if latitude is not None else 0
            longitude = float(longitude) if longitude is not None else 0
        except (ValueError, TypeError):
            return Response(
                {"error": "Latitud o longitud inválidas"},
                status=400
            )

        # determinar si se calculará distancia
        usar_distancia = not (latitude == 0 and longitude == 0)

        user_point = None
        if usar_distancia:
            user_point = Point(longitude, latitude, srid=4326)

        # ==========================================
        # 🕒 FECHA BASE PARA ACTIVIDAD
        # ==========================================
        hace_30_dias = timezone.now() - timedelta(days=30)

        # ==========================================
        # 📍 SUBQUERY ÚLTIMA UBICACIÓN
        # evita consultar ubicación dentro del for
        # ==========================================
        ultima_ubicacion = (
            UBICACIONES.objects
            .filter(id_user=OuterRef("id_user"))
            .order_by("-fecha_actualizacion")
        )

        # ==========================================
        # 🔍 CONSULTA PRINCIPAL OPTIMIZADA
        # ==========================================
        publicaciones = (
            ARTICULOS_VENTA.objects
            .filter(
                id_articulo_id=id_articulo,
                estado="activo",
                id_user__rol="tienda",
                id_user__estado="activo",
                id_user__suscripciones__estado="vigente"
            )
            .select_related(
                "id_user",
                "id_user__negocio",
                "id_articulo"
            )
            .annotate(
                # ==========================================
                # ⭐ CALIFICACIONES
                # ==========================================
                total_positivos=Count(
                    "id_user__calificaciones_recibidas",
                    filter=Q(
                        id_user__calificaciones_recibidas__tipo_calificacion="positivo"
                    ),
                    distinct=True
                ),

                total_negativos=Count(
                    "id_user__calificaciones_recibidas",
                    filter=Q(
                        id_user__calificaciones_recibidas__tipo_calificacion="negativo"
                    ),
                    distinct=True
                ),

                # ==========================================
                # 🔥 ACTIVIDAD ÚLTIMOS 30 DÍAS
                # ==========================================
                actividad_count=Count(
                    "id_user__articulos_venta",
                    filter=Q(
                        id_user__articulos_venta__estado="activo",
                        id_user__articulos_venta__fecha__gte=hace_30_dias
                    ),
                    distinct=True
                ),

                # ==========================================
                # 📍 ÚLTIMA UBICACIÓN
                # ==========================================
                latitud_actual=Subquery(
                    ultima_ubicacion.values("latitud")[:1]
                ),

                longitud_actual=Subquery(
                    ultima_ubicacion.values("longitud")[:1]
                ),

                geometria_actual=Subquery(
                    ultima_ubicacion.values("geometria_user")[:1]
                )
            )
            .order_by("-fecha")
        )

        resultado = []

        # ==========================================
        # 🔄 PROCESAR RESULTADO FINAL
        # ==========================================
        for venta in publicaciones:

            usuario = venta.id_user
            negocio = getattr(usuario, "negocio", None)

            # ==========================================
            # 📍 DISTANCIA
            # ==========================================
            distancia = None

            if usar_distancia and venta.geometria_actual:
                distancia = round(
                    venta.geometria_actual.distance(user_point) * 111000,
                    2
                )

            # ==========================================
            # ⭐ SCORE REPUTACIÓN
            # ==========================================
            total_positivos = venta.total_positivos
            total_negativos = venta.total_negativos

            total_calificaciones = (
                total_positivos + total_negativos
            )

            score_recomendacion = (
                round(
                    (total_positivos / total_calificaciones) * 100,
                    1
                )
                if total_calificaciones > 0
                else 0
            )

            # ==========================================
            # 🔥 SCORE ACTIVIDAD
            # peso máximo: 15 puntos
            # ==========================================
            actividad_score = min(
                venta.actividad_count * 3,
                15
            )

            # ==========================================
            # 📍 SCORE DISTANCIA
            # peso máximo: 50 puntos
            # ==========================================
            if distancia is None:
                distancia_score = 0
            elif distancia <= 50:
                distancia_score = 50
            elif distancia <= 100:
                distancia_score = 45
            elif distancia <= 200:
                distancia_score = 40
            elif distancia <= 300:
                distancia_score = 35
            elif distancia <= 500:
                distancia_score = 25
            else:
                distancia_score = 15

            # ==========================================
            # ⭐ SCORE REPUTACIÓN
            # peso máximo: 35 puntos
            # ==========================================
            reputacion_score = round(
                score_recomendacion * 0.35,
                2
            )

            # ==========================================
            # 🏆 RANKING FINAL
            # ==========================================
            ranking_total = round(
                distancia_score +
                reputacion_score +
                actividad_score,
                2
            )

            resultado.append({
                "id_venta": venta.id_venta,
                "id_user": usuario.id_user,
                "nombre_usuario": usuario.nombre,
                "nombre_negocio": negocio.nombre_negocio if negocio else "",
                "descripcion_negocio": negocio.descripcion if negocio else "",
                "descripcion_publicacion": venta.descripcion,
                "precio": str(venta.precio),
                "fecha": venta.fecha,

                "latitud": float(venta.latitud_actual) if venta.latitud_actual else None,
                "longitud": float(venta.longitud_actual) if venta.longitud_actual else None,
                "distancia_m": distancia,

                # reputación
                "total_positivos": total_positivos,
                "total_negativos": total_negativos,
                "score_recomendacion": score_recomendacion,

                # ranking
                "ranking_score": ranking_total,
                "actividad_score": actividad_score,
                "distancia_score": distancia_score,
                "reputacion_score": reputacion_score,
            })

        # ==========================================
        # 🏆 ORDENAR POR SCORE DESCENDENTE, MENOR DISTANCIA Y MAS ACTIVO
        # ==========================================
        resultado.sort(
            key=lambda x: (
                -x["ranking_score"],
                x["distancia_m"] if x["distancia_m"] is not None else 999999,
                -x["actividad_score"]
            )
        )

        return Response({
            "count": len(resultado),
            "results": resultado
        })

class DetalleVendedorAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        id_venta = request.query_params.get("id_venta")

        if not id_venta:
            return Response(
                {"error": "id_venta es requerido"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # ==========================================
            # 🔍 PUBLICACIÓN SELECCIONADA
            # ==========================================
            venta_actual = (
                ARTICULOS_VENTA.objects
                .select_related(
                    "id_user",
                    "id_user__negocio",
                    "id_articulo"
                )
                .get(
                    id_venta=id_venta,
                    estado="activo"
                )
            )

        except ARTICULOS_VENTA.DoesNotExist:
            return Response(
                {"error": "No se encontró la publicación"},
                status=status.HTTP_404_NOT_FOUND
            )

        usuario = venta_actual.id_user
        negocio = getattr(usuario, "negocio", None)

        # ==========================================
        # ⭐ CALIFICACIONES DEL COMERCIANTE
        # ==========================================
        stats = CALIFICACIONES.objects.filter(
            id_user_vendedor=usuario
        ).aggregate(
            total_positivos=Count(
                "id_calificacion",
                filter=Q(tipo_calificacion="positivo")
            ),
            total_negativos=Count(
                "id_calificacion",
                filter=Q(tipo_calificacion="negativo")
            )
        )

        total_positivos = stats["total_positivos"] or 0
        total_negativos = stats["total_negativos"] or 0

        total_calificaciones = total_positivos + total_negativos

        score_recomendacion = (
            round((total_positivos / total_calificaciones) * 100, 1)
            if total_calificaciones > 0
            else 0
        )

        # ==========================================
        # 🛒 OTRAS PUBLICACIONES DEL VENDEDOR
        # ==========================================
        otras_publicaciones = (
            ARTICULOS_VENTA.objects
            .select_related("id_articulo")
            .filter(
                id_user=usuario,
                estado="activo"
            )
            .exclude(
                id_articulo=venta_actual.id_articulo
            )
            .values(
                "id_venta",
                "id_articulo__id_articulo",
                "id_articulo__nombre",
                "descripcion",
                "precio"
            )
            .order_by("-fecha")
        )

        articulos_venta = [
            {
                "id_venta": item["id_venta"],
                "id_articulo": item["id_articulo__id_articulo"],
                "nombre_articulo": item["id_articulo__nombre"],
                "descripcion": item["descripcion"],
                "precio": str(item["precio"]),
            }
            for item in otras_publicaciones
        ]

        # ==========================================
        # 📦 RESPUESTA FINAL
        # ==========================================
        data = {
            "id_venta": venta_actual.id_venta,
            "id_user": usuario.id_user,
            "nombre_usuario": usuario.nombre,
            "nombre_negocio": negocio.nombre_negocio if negocio else "",
            "descripcion_negocio": negocio.descripcion if negocio else "",
            "descripcion_publicacion": venta_actual.descripcion,

            # ⭐ reputación
            "total_positivos": total_positivos,
            "total_negativos": total_negativos,
            "score_recomendacion": score_recomendacion,

            # 🛒 otras publicaciones
            "articulos_venta": articulos_venta
        }

        return Response(data, status=status.HTTP_200_OK)