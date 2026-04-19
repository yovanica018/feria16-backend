from rest_framework import generics
from .models import AREA
from .serializers import AreaGeoSerializer
from rest_framework.permissions import AllowAny

from django.shortcuts import get_object_or_404

from rest_framework.views import APIView
from rest_framework.response import Response

from django.contrib.gis.geos import Point
from django.contrib.gis.db.models.functions import Distance

from catalogo.models import ARTICULO_BASE
from django.contrib.postgres.search import TrigramSimilarity
from django.db.models import Q, Case, When, Value, IntegerField
from django.db.models.functions import Trim, Lower
import json
from django.core.serializers import serialize

from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.db.models import F


class AreaListAPIView(generics.ListAPIView):
    queryset = AREA.objects.exclude(geometria__isnull=True)
    serializer_class = AreaGeoSerializer
    permission_classes = [AllowAny]  # 👈 IMPORTANTE

class AreaFeriaAPIView(generics.RetrieveAPIView):
    serializer_class = AreaGeoSerializer
    permission_classes = [AllowAny]

    def get_object(self):
        return get_object_or_404(
            AREA,
            id_area=1,
            geometria__isnull=False
        )

class VerificarUbicacionFeriaAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        lat = request.data.get("latitude")
        lng = request.data.get("longitude")

        if not lat or not lng:
            return Response({"error": "Coordenadas inválidas"}, status=400)

        punto = Point(float(lng), float(lat), srid=4326)

        try:
            area = AREA.objects.get(id_area=1)
        except AREA.DoesNotExist:
            return Response({"error": "Área no encontrada"}, status=404)

        if area.geometria and area.geometria.contains(punto):
            return Response({
                "dentro": True,
                "mensaje": "Se encuentra dentro de la feria"
            })

        return Response({
            "dentro": False,
            "mensaje": "No se encuentra dentro del área de la Feria 16 de Julio"
        })


class AreasPorArticuloAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):

        id_articulo = request.GET.get("id_articulo")
        latitude = request.GET.get("latitude")
        longitude = request.GET.get("longitude")

        # ==========================================
        # 🔴 VALIDACIÓN
        # ==========================================
        if not id_articulo:
            return Response({"error": "Falta parámetro id_articulo"}, status=400)

        try:
            id_articulo = int(id_articulo)
        except ValueError:
            return Response({"error": "id_articulo inválido"}, status=400)

        try:
            latitude = float(latitude) if latitude is not None else 0
            longitude = float(longitude) if longitude is not None else 0
        except (ValueError, TypeError):
            return Response({"error": "Latitud o longitud inválidas"}, status=400)

        usar_distancia = not (latitude == 0 and longitude == 0)

        user_point = None
        if usar_distancia:
            user_point = Point(longitude, latitude, srid=4326)

        # ==========================================
        # 🔎 BUSCAR ARTICULO
        # ==========================================
        try:
            articulo = (
                ARTICULO_BASE.objects
                .select_related("id_subrubro__id_rubro")
                .get(id_articulo=id_articulo)
            )
        except ARTICULO_BASE.DoesNotExist:
            return Response({
                "rubro": "",
                "subrubro": "",
                "count": 0,
                "results": []
            }, status=200)

        # ==========================================
        # 📦 OBTENER AREAS RELACIONADAS (ManyToMany)
        # ==========================================
        areas = articulo.areas.all()

        if usar_distancia:
            areas = areas.annotate(
                distancia=Distance("geometria", user_point)
            ).order_by("distancia")

        # ==========================================
        # 📤 FORMATEAR RESPUESTA
        # ==========================================
        response_data = []

        for area in areas:

            distancia = None

            if usar_distancia and hasattr(area, "distancia") and area.distancia:
                distancia = round(area.distancia.m, 2)

            geometry = None
            if area.geometria:
                geometry = json.loads(area.geometria.geojson)

            response_data.append({
                "id_area": area.id_area,
                "descripcion": area.descripcion,
                "color": area.color,
                "tipo_area": area.tipo_area,
                "distancia_m": distancia,
                "geometry": geometry,
            })

        return Response({
            "rubro": articulo.id_subrubro.id_rubro.nombre,
            "subrubro": articulo.id_subrubro.nombre,
            "count": len(response_data),
            "results": response_data
        })

class AreaGeometryAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, id_area):

        area = get_object_or_404(
            AREA,
            id_area=id_area,
            geometria__isnull=False
        )

        # Convertimos a GeoJSON
        geojson = json.loads(
            serialize(
                "geojson",
                [area],
                geometry_field="geometria",
                fields=()
            )
        )

        return Response({
            "id_area": area.id_area,
            "tipo_area": area.tipo_area,
            "color": area.color,
            "geometry": geojson["features"][0]["geometry"]
        })

@require_GET
def DetalleArea(request):

    area_id = request.GET.get("id_area")
    articulo_id = request.GET.get("id_articulo")

    if not area_id:
        return JsonResponse(
            {"error": "id_area requerido"},
            status=400
        )

    if not articulo_id:
        return JsonResponse(
            {"error": "id_articulo requerido"},
            status=400
        )

    # ==========================================
    # 🔍 BUSCAR ÁREA
    # ==========================================
    try:
        area = (
            AREA.objects
            .prefetch_related(
                "id_articulo__id_subrubro__id_rubro"
            )
            .get(pk=area_id)
        )

    except AREA.DoesNotExist:
        return JsonResponse(
            {"error": "Área no encontrada"},
            status=404
        )

    # ==========================================
    # 🔴 ARTÍCULO BUSCADO (EXACTO)
    # ==========================================
    try:
        articulo_principal = (
            area.id_articulo
            .select_related("id_subrubro__id_rubro")
            .get(id_articulo=articulo_id)
        )

    except ARTICULO_BASE.DoesNotExist:
        return JsonResponse(
            {"error": "El artículo no pertenece a esta área"},
            status=404
        )

    # ==========================================
    # 🟠 OTROS ARTÍCULOS EN LA MISMA ÁREA
    # ==========================================
    articulos_misma_area = (
        area.id_articulo
        .exclude(id_articulo=articulo_id)
        .values_list("nombre", flat=True)
        .distinct()
    )

    # ==========================================
    # 🔵 ÁREAS QUE INTERSECTAN
    # ==========================================
    areas_intersectadas = (
        AREA.objects
        .filter(
            geometria__intersects=area.geometria
        )
        .exclude(id_area=area.id_area)
    )

    # ==========================================
    # 🟢 ARTÍCULOS EN ÁREAS INTERSECTADAS
    # ==========================================
    articulos_vecinos = (
        ARTICULO_BASE.objects
        .filter(
            areas__in=areas_intersectadas
        )
        .exclude(id_articulo=articulo_id)
        .exclude(nombre__in=articulos_misma_area)
        .values_list("nombre", flat=True)
        .distinct()
    )

    # ==========================================
    # 🔥 COMBINAR ARTÍCULOS RELACIONADOS
    # ==========================================
    articulos_relacionados = list(articulos_misma_area)

    for nombre in articulos_vecinos:
        if nombre not in articulos_relacionados:
            articulos_relacionados.append(nombre)

    # ==========================================
    # 📦 RESPONSE
    # ==========================================
    data = {
        "titulo": area.descripcion,
        "articulo": articulo_principal.nombre,
        "rubro": articulo_principal.id_subrubro.id_rubro.nombre,
        "subrubro": articulo_principal.id_subrubro.nombre,
        "descripcion_articulo": articulo_principal.descripcion,
        "articulos_area": articulos_relacionados
    }

    return JsonResponse(data)