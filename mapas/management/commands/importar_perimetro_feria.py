import sqlite3
from pathlib import Path
from django.core.management.base import BaseCommand
from django.db import transaction
from mapas.models import AREA

BASE_DIR = Path(__file__).resolve().parent
SQLITE_PATH = BASE_DIR / "feria16_perimetro.db"


class Command(BaseCommand):
    help = "Importa el perímetro de la Feria 16 de Julio como id_area=1"

    @transaction.atomic
    def handle(self, *args, **options):

        if not SQLITE_PATH.exists():
            self.stdout.write(self.style.ERROR("No se encontró feria16_perimetro.db"))
            return

        conn = sqlite3.connect(SQLITE_PATH)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT nombre, tipo, puntos
            FROM zonas
            LIMIT 1
        """)

        row = cursor.fetchone()

        if not row:
            self.stdout.write(self.style.ERROR("No hay datos en SQLite"))
            return

        nombre, tipo, puntos = row

        # 🔥 Validamos que sea polygon
        if tipo.lower() != "polygon":
            self.stdout.write(self.style.ERROR("El tipo no es polygon"))
            return

        # 🔥 Borramos si ya existe id_area=1
        AREA.objects.filter(id_area=1).delete()

        # 🔥 Creamos exactamente como viene
        AREA.objects.create(
            id_area=1,
            tipo_area="polygon",   # tu modelo usa choice en español
            coordenadas=puntos,     # EXACTAMENTE como viene
            descripcion=nombre,
            color="#FF0000"
        )

        conn.close()

        self.stdout.write(
            self.style.SUCCESS("Perímetro importado correctamente en id_area=1")
        )