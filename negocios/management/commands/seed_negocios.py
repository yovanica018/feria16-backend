import random
from django.core.management.base import BaseCommand

from usuarios.models import UserAPP
from negocios.models import NEGOCIO


class Command(BaseCommand):
    help = 'Genera negocios ficticios para usuarios'

    def handle(self, *args, **kwargs):

        usuarios = UserAPP.objects.filter(
            rol__in=["comerciante", "tienda"],
            estado="activo"
        )

        if not usuarios.exists():
            self.stdout.write(self.style.WARNING("⚠️ No hay usuarios válidos"))
            return

        nombres_base = [
            "Comercial", "Importadora", "Distribuidora",
            "Tienda", "Centro", "Ventas", "Ofertas"
        ]

        rubros_fake = [
            "Ropa", "Electrónica", "Calzados",
            "Accesorios", "Herramientas", "Comida"
        ]

        creados = 0

        for user in usuarios:

            # 🔒 Evitar duplicados (OneToOne)
            if hasattr(user, 'negocio'):
                continue

            nombre_negocio = f"{random.choice(nombres_base)} {random.choice(rubros_fake)} {user.id_user}"

            descripcion = f"Negocio de {user.nombre} especializado en productos variados."

            negocio = NEGOCIO(
                id_user=user,
                nombre_negocio=nombre_negocio,
                descripcion=descripcion
            )

            try:
                negocio.save()
                creados += 1
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Error con usuario {user.id_user}: {e}")
                )

        self.stdout.write(self.style.SUCCESS(f"✅ {creados} negocios creados"))