import random
from django.core.management.base import BaseCommand
from django.contrib.gis.geos import Point

from usuarios.models import UserAPP, UBICACIONES

from decimal import Decimal, ROUND_HALF_UP

class Command(BaseCommand):
    help = 'Genera ubicaciones ficticias para usuarios'

    def handle(self, *args, **kwargs):

        usuarios = UserAPP.objects.filter(
            rol__in=["comerciante", "tienda"],
            estado="activo"
        )

        if not usuarios.exists():
            self.stdout.write(self.style.WARNING("⚠️ No hay usuarios válidos"))
            return

        # 📍 Bounding box feria 16 de julio
        LAT_MIN, LAT_MAX = -16.4900, -16.4700
        LNG_MIN, LNG_MAX = -68.2000, -68.1700

        creados = 0

        for user in usuarios:

            # evitar duplicados si ya tiene ubicación
            if user.ubicaciones.exists():
                continue

            def generar_decimal(min_val, max_val):
                valor = random.uniform(min_val, max_val)
                return Decimal(valor).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)

            lat = generar_decimal(LAT_MIN, LAT_MAX)
            lng = generar_decimal(LNG_MIN, LNG_MAX)

            tipo = random.choices(
                ["fija", "movil"],
                weights=[0.7, 0.3]
            )[0]

            punto = Point(float(lng), float(lat))

            ubicacion = UBICACIONES(
                id_user=user,
                latitud=lat,
                longitud=lng,
                geometria_user=punto,
                tipo=tipo
            )

            try:
                ubicacion.save()
                creados += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error con usuario {user.id_user}: {e}"))

        self.stdout.write(self.style.SUCCESS(f"✅ {creados} ubicaciones creadas"))