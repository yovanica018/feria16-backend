from django.contrib import admin
from .models import CALIFICACIONES, BUSQUEDAS

@admin.register(CALIFICACIONES)
class CalificacionAdmin(admin.ModelAdmin):
    list_display = (
        'id_calificacion',
        'id_user',
        'id_user_vendedor',
        'tipo_calificacion',
        'fecha'
    )

    list_filter = (
        'tipo_calificacion',
        'fecha'
    )

    search_fields = (
        'id_user__nombre',
        'id_user_vendedor__nombre'
    )

@admin.register(BUSQUEDAS)
class BusquedaAdmin(admin.ModelAdmin):
    list_display = ('id_busqueda', 'id_user', 'texto_busqueda', 'num_resultados', 'fecha')
    search_fields = ('texto_busqueda',)