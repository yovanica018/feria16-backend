import random
from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from usuarios.models import UserAPP
from suscripciones.models import SUSCRIPCIONES


class Command(BaseCommand):
    help = 'Genera suscripciones ficticias para usuarios'

    def handle(self, *args, **kwargs):

        usuarios = UserAPP.objects.filter(
            rol__in=["comerciante", "tienda"],
            estado="activo"
        )

        if not usuarios.exists():
            self.stdout.write(self.style.WARNING("⚠️ No hay usuarios válidos"))
            return

        creados = 0

        for user in usuarios:

            # 🔒 Evitar duplicados
            if SUSCRIPCIONES.objects.filter(id_user=user).exists():
                continue

            fecha_inicio = timezone.now()
            fecha_final = fecha_inicio + timedelta(days=30)

            suscripcion = SUSCRIPCIONES(
                id_user=user,
                tipo=random.choice(["basico", "premium"]),
                fecha_inicio=fecha_inicio,
                fecha_final=fecha_final,
                estado="vigente",
                costo=Decimal(random.choice(["50.00", "100.00", "150.00"]))
            )

            try:
                suscripcion.save()
                creados += 1
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Error con usuario {user.id_user}: {e}")
                )

        self.stdout.write(self.style.SUCCESS(f"✅ {creados} suscripciones creadas"))