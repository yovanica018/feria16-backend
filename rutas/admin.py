from django.contrib import admin
from .models import HISTORIAL_RUTAS

@admin.register(HISTORIAL_RUTAS)
class HistorialRutasAdmin(admin.ModelAdmin):
    list_display = ('id_rutas', 'id_user', 'id_area')
