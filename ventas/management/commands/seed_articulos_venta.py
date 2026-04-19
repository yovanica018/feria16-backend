import random
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone

from usuarios.models import UserAPP
from catalogo.models import SUBRUBRO_BASE, ARTICULO_BASE
from ventas.models import ARTICULOS_VENTA


class Command(BaseCommand):
    help = 'Genera artículos de venta ficticios'

    def handle(self, *args, **kwargs):

        usuarios = UserAPP.objects.filter(
            rol__in=["comerciante", "tienda"],
            estado="activo"
        )

        if not usuarios.exists():
            self.stdout.write(self.style.WARNING("⚠️ No hay usuarios válidos"))
            return

        total_creados = 0

        for user in usuarios:

            # 🔒 Debe tener negocio
            if not hasattr(user, 'negocio'):
                continue

            # 🔒 Evitar duplicar ventas si ya tiene
            if ARTICULOS_VENTA.objects.filter(id_user=user).exists():
                continue

            # 🎯 Elegir un subrubro
            subrubros = SUBRUBRO_BASE.objects.all()
            if not subrubros.exists():
                continue

            subrubro = random.choice(subrubros)

            # 📦 Obtener artículos de ese subrubro
            articulos = list(
                ARTICULO_BASE.objects.filter(id_subrubro=subrubro)
            )

            if not articulos:
                continue

            cantidad = random.randint(2, min(5, len(articulos)))
            seleccionados = random.sample(articulos, cantidad)

            for articulo in seleccionados:

                precio = self.generar_precio(articulo.nombre)

                descripcion = self.generar_descripcion(
                    articulo.nombre,
                    user.negocio.nombre_negocio
                )

                venta = ARTICULOS_VENTA(
                    id_user=user,
                    id_articulo=articulo,
                    descripcion=descripcion,
                    precio=precio,
                    fecha=timezone.now(),
                    estado="activo"
                )

                try:
                    venta.save()
                    total_creados += 1
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(
                            f"Error con usuario {user.id_user}: {e}"
                        )
                    )

        self.stdout.write(self.style.SUCCESS(f"✅ {total_creados} ventas creadas"))

    # 💰 Lógica de precios
    def generar_precio(self, nombre):

        nombre_lower = nombre.lower()

        if any(p in nombre_lower for p in ["polera", "camisa", "pantalon", "ropa"]):
            return Decimal(random.randint(30, 150))

        elif any(p in nombre_lower for p in ["celular", "tv", "laptop", "electro"]):
            return Decimal(random.randint(100, 1000))

        elif any(p in nombre_lower for p in ["comida", "hamburguesa", "salteña"]):
            return Decimal(random.randint(5, 50))

        else:
            return Decimal(random.randint(20, 200))

    # 📝 Descripciones realistas
    def generar_descripcion(self, articulo, negocio):

        frases = [
            "Producto de buena calidad",
            "Disponible en diferentes modelos",
            "Garantía incluida",
            "Precio accesible",
            "Entrega inmediata"
        ]

        return f"{articulo} en {negocio}. {random.choice(frases)}."