from django.core.management.base import BaseCommand
from django.db import transaction

from mapas.models import AREA, AREA_VECINA


class Command(BaseCommand):

    help = "Calcula áreas vecinas considerando geometría y artículos compartidos"

    def handle(self, *args, **kwargs):

        self.stdout.write("Calculando áreas vecinas (modelo híbrido)...")

        total = 0

        with transaction.atomic():

            AREA_VECINA.objects.all().delete()

            areas = AREA.objects.exclude(geometria__isnull=True).prefetch_related("id_articulo")

            for area in areas:

                if area.id_area == 1:
                    continue

                # ==========================================
                # 🔹 1. VECINAS POR GEOMETRÍA
                # ==========================================
                vecinas_geo = AREA.objects.filter(
                    geometria__intersects=area.geometria
                ).exclude(
                    id_area=area.id_area
                )

                # ==========================================
                # 🔹 2. VECINAS POR ARTÍCULO (MISMA ZONA LÓGICA)
                # ==========================================
                articulos = area.id_articulo.all()

                vecinas_articulo = AREA.objects.filter(
                    id_articulo__in=articulos
                ).exclude(
                    id_area=area.id_area
                )

                # ==========================================
                # 🔥 UNIÓN DE AMBAS
                # ==========================================
                vecinas = (vecinas_geo | vecinas_articulo).distinct()

                for v in vecinas:

                    AREA_VECINA.objects.create(
                        area=area,
                        area_vecina=v
                    )

                    total += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"✔ Áreas vecinas actualizadas correctamente. Registros creados: {total}"
            )
        )