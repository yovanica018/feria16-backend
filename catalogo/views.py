from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from django.db.models import Count, Q, Case, When, IntegerField, Value
from django.db.models.functions import Lower
from django.db.models import Func
from django.contrib.postgres.search import TrigramSimilarity

from catalogo.models import ARTICULO_BASE
from ventas.models import ARTICULOS_VENTA

import unicodedata


# ==========================================
# 🔧 FUNCIONES AUXILIARES
# ==========================================

def quitar_tildes(texto):
    return ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    )


class Unaccent(Func):
    function = 'unaccent'
    template = "%(function)s(%(expressions)s)"


# ==========================================
# 🔍 VIEW PRINCIPAL
# ==========================================

class ArticuloSearchView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):

        search = request.query_params.get('search', '').strip()

        if not search:
            return Response([])

        words = search.split()

        # 🔥 NORMALIZACIÓN REAL (CLAVE)
        words_clean = [quitar_tildes(w.lower()) for w in words]
        search_clean = quitar_tildes(search.lower())

        # ==========================================
        # 🔎 QUERY BUILDER
        # ==========================================
        def build_queryset(model, field_name, extra_filters=None):

            if extra_filters is None:
                extra_filters = Q()

            queryset = (
                model.objects
                .annotate(
                    nombre_unaccent=Unaccent(Lower(field_name))
                )
            )

            # 🔥 FILTRO SIN TILDES
            for word in words_clean:
                queryset = queryset.filter(
                    nombre_unaccent__icontains=word
                )

            return (
                queryset
                .annotate(
                    exact_match=Case(
                        When(nombre_unaccent=search_clean, then=1),
                        default=0,
                        output_field=IntegerField()
                    ),
                    similarity=TrigramSimilarity(
                        'nombre_unaccent',
                        Value(search_clean)
                    )
                )
                .filter(extra_filters)
                .order_by('-exact_match', '-similarity')
            )

        # ==========================================
        # 📦 ARTICULOS BASE + AREAS
        # ==========================================
        articulos = (
            build_queryset(ARTICULO_BASE, 'nombre')
            .select_related('id_subrubro__id_rubro')
            .annotate(
                cantidad_areas=Count('areas', distinct=True)
            )
        )

        resumen = {}

        for articulo in articulos:

            resumen[articulo.id_articulo] = {
                'id_articulo': articulo.id_articulo,
                'nombre': articulo.nombre,
                'rubro': articulo.id_subrubro.id_rubro.nombre,
                'subrubro': articulo.id_subrubro.nombre,
                'cantidad_areas': articulo.cantidad_areas,
                'cantidad_comerciantes': 0,
                'cantidad_tiendas': 0,
            }

        # ==========================================
        # 👤 COMERCIANTES (SIN TILDES)
        # ==========================================
        comerciantes = (
            ARTICULOS_VENTA.objects
            .annotate(
                nombre_unaccent=Unaccent(Lower('id_articulo__nombre'))
            )
            .filter(
                estado='activo',
                id_user__rol='comerciante',
                id_user__estado='activo',
                id_user__suscripciones__estado='vigente',
                nombre_unaccent__icontains=search_clean
            )
            .values('id_articulo')
            .annotate(
                cantidad=Count('id_user', distinct=True)
            )
        )

        for item in comerciantes:
            articulo_id = item['id_articulo']

            if articulo_id in resumen:
                resumen[articulo_id]['cantidad_comerciantes'] = item['cantidad']

        # ==========================================
        # 🏬 TIENDAS (SIN TILDES)
        # ==========================================
        tiendas = (
            ARTICULOS_VENTA.objects
            .annotate(
                nombre_unaccent=Unaccent(Lower('id_articulo__nombre'))
            )
            .filter(
                estado='activo',
                id_user__rol='tienda',
                id_user__estado='activo',
                id_user__suscripciones__estado='vigente',
                nombre_unaccent__icontains=search_clean
            )
            .values('id_articulo')
            .annotate(
                cantidad=Count('id_user', distinct=True)
            )
        )

        for item in tiendas:
            articulo_id = item['id_articulo']

            if articulo_id in resumen:
                resumen[articulo_id]['cantidad_tiendas'] = item['cantidad']

        # ==========================================
        # 🔥 FILTRO FINAL (CLAVE DE NEGOCIO)
        # ==========================================
        resultado = [
            item for item in resumen.values()
            if (
                item['cantidad_areas'] > 0 or
                item['cantidad_comerciantes'] > 0 or
                item['cantidad_tiendas'] > 0
            )
        ]

        # 🔥 LIMITAR RESULTADOS
        resultado = resultado[:20]

        return Response(resultado)