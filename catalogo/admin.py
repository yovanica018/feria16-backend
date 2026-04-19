from django.contrib import admin
from .models import RUBRO_BASE, SUBRUBRO_BASE, ARTICULO_BASE

@admin.register(ARTICULO_BASE)
class ArticuloBaseAdmin(admin.ModelAdmin):
    search_fields = ['nombre']  # 🔥 obligatorio para autocomplete