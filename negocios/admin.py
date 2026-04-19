from django.contrib import admin
from .models import NEGOCIO

@admin.register(NEGOCIO)
class NegocioAdmin(admin.ModelAdmin):
    list_display = ('id_negocio', 'nombre_negocio', 'id_user')
    search_fields = ('nombre_negocio',)
    list_filter = ('id_user',)