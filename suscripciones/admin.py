from django.contrib import admin
from .models import SUSCRIPCIONES

@admin.register(SUSCRIPCIONES)
class SuscripcionAdmin(admin.ModelAdmin):
    list_display = ('id_suscripcion', 'id_user', 'tipo', 'estado', 'fecha_inicio', 'fecha_final')
    list_filter = ('tipo', 'estado')
    search_fields = ('id_user__email',)