from django.contrib import admin
from .models import ARTICULOS_VENTA, GALERIA, OFERTAS

@admin.register(ARTICULOS_VENTA)
class ArticuloVentaAdmin(admin.ModelAdmin):
    list_display = (
        'id_venta',
        'articulo_nombre',
        'id_user',
        'precio',
        'estado',
        'fecha'
    )

    list_filter = (
        'estado',
        'id_articulo',
    )

    search_fields = (
        'id_articulo__nombre',
        'id_user__nombre',
    )

    autocomplete_fields = ['id_articulo', 'id_user']

    def articulo_nombre(self, obj):
        return obj.id_articulo.nombre
    articulo_nombre.short_description = 'Artículo'

@admin.register(GALERIA)
class GaleriaAdmin(admin.ModelAdmin):
    list_display = ('id_galeria', 'id_venta', 'tipo')
    list_filter = ('tipo',)

@admin.register(OFERTAS)
class OfertaAdmin(admin.ModelAdmin):
    list_display = ('id_oferta', 'id_venta', 'precio', 'estado', 'fecha_inicio', 'fecha_final')
    list_filter = ('estado',)