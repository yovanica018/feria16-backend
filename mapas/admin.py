from django.contrib import admin
from .models import AREA

@admin.register(AREA)
class AreaAdmin(admin.ModelAdmin):
    list_display = ('id_area', 'tipo_area', 'color')
    list_filter = ('tipo_area',)

