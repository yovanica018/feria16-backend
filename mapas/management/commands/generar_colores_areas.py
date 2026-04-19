import colorsys
from django.core.management.base import BaseCommand
from mapas.models import AREA


class Command(BaseCommand):
    help = "Asigna colores oscuros y únicos a cada área"

    def hsv_to_hex(self, h):
        """
        Genera colores oscuros y bien visibles en mapa diurno
        """
        r, g, b = colorsys.hsv_to_rgb(
            h,
            0.85,   # 🔥 más saturación
            0.55    # 🔥 menos brillo = más oscuro
        )

        return '#{:02x}{:02x}{:02x}'.format(
            int(r * 255),
            int(g * 255),
            int(b * 255)
        )

    def handle(self, *args, **kwargs):

        # 🔴 perímetro fijo
        try:
            feria = AREA.objects.get(id_area=1)
            feria.color = "#FF0000"   # 🔥 rojo oscuro
            feria.save(update_fields=["color"])
            self.stdout.write("Área 1 → rojo oscuro")
        except AREA.DoesNotExist:
            pass

        # 🔵 áreas normales
        areas = (
            AREA.objects
            .exclude(id_area=1)
            .order_by("id_area")
        )

        total = areas.count()

        if total == 0:
            self.stdout.write("No hay áreas para procesar")
            return

        golden_ratio = 0.61803398875
        hue = 0.15

        actualizados = 0

        for area in areas:

            hue = (hue + golden_ratio) % 1

            color = self.hsv_to_hex(hue)

            area.color = color
            area.save(update_fields=["color"])

            actualizados += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"✔ Colores oscuros asignados a {actualizados} áreas"
            )
        )