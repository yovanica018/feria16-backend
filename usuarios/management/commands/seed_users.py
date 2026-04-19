import random
import uuid
from django.core.management.base import BaseCommand
from django.utils import timezone

from usuarios.models import UserAPP


class Command(BaseCommand):
    help = 'Genera usuarios ficticios para pruebas'

    def handle(self, *args, **kwargs):

        nombres = [
            "Juan", "Carlos", "Luis", "Pedro", "Jorge", "Miguel",
            "Andrés", "Fernando", "Diego", "Raúl",
            "María", "Ana", "Lucía", "Carmen", "Sofía",
            "Valeria", "Gabriela", "Daniela", "Paola", "Rosa"
        ]

        apellidos = [
            "Pérez", "García", "Rodríguez", "López", "Martínez",
            "González", "Hernández", "Sánchez", "Ramírez", "Torres",
            "Flores", "Rivera", "Vargas", "Castro", "Rojas"
        ]

        roles = ["comerciante", "tienda"]

        total = 100
        creados = 0



        for _ in range(total):

            nombre_completo = f"{random.choice(nombres)} {random.choice(apellidos)}"

            uid_fake = str(uuid.uuid4())  # UID único tipo Firebase

            user = UserAPP(
                UID=uid_fake,
                nombre=nombre_completo,
                rol=random.choice(roles),
                estado="activo",
                proveedor="google",
                ultimo_inicio=timezone.now()
            )

            user.save()  # 🔥 Aquí se genera codigo_user automáticamente

            creados += 1

        self.stdout.write(self.style.SUCCESS(f'✅ {creados} usuarios creados correctamente'))