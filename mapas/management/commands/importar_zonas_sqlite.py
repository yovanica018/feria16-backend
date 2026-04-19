import sqlite3
import json
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import transaction

from mapas.models import AREA
from catalogo.models import ARTICULO_BASE, SUBRUBRO_BASE, RUBRO_BASE

BASE_DIR = Path(__file__).resolve().parent
SQLITE_PATH = BASE_DIR / 'feria16_exportada.db'

COLOR_POR_DEFECTO = '#FF5722'


def limpiar(texto):
    if not texto:
        return ""
    return texto.strip()


def normalizar(texto):
    return limpiar(texto).lower()


class Command(BaseCommand):
    help = 'Importa zonas desde SQLite (estructura nueva optimizada)'

    def handle(self, *args, **options):

        if not SQLITE_PATH.exists():
            self.stdout.write(self.style.ERROR(f'No se encontró: {SQLITE_PATH}'))
            return

        conn = sqlite3.connect(SQLITE_PATH)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT nombre, rubro, subrubro, tipo, puntos
            FROM zonas
        """)

        rows = cursor.fetchall()
        total = len(rows)

        self.stdout.write(f'Registros encontrados: {total}')

        creados = 0
        reutilizados = 0
        relaciones = 0

        with transaction.atomic():

            for i, row in enumerate(rows, start=1):

                nombre, rubro_nombre, subrubro_nombre, tipo_area, puntos = row

                # =============================
                # 🔹 NORMALIZACIÓN
                # =============================
                nombre = limpiar(nombre)
                rubro_nombre = limpiar(rubro_nombre)
                subrubro_nombre = limpiar(subrubro_nombre)

                nombre_norm = normalizar(nombre)
                rubro_norm = normalizar(rubro_nombre)
                subrubro_norm = normalizar(subrubro_nombre)

                # =============================
                # 🔹 RUBRO_BASE
                # =============================
                rubro, _ = RUBRO_BASE.objects.get_or_create(
                    nombre__iexact=rubro_norm,
                    defaults={
                        'nombre': rubro_nombre,
                        'descripcion': f'Rubro {rubro_nombre}'
                    }
                )

                # Fix cuando existe pero con diferente formato
                if rubro.nombre != rubro_nombre:
                    rubro.nombre = rubro_nombre
                    rubro.save()

                # =============================
                # 🔹 SUBRUBRO_BASE
                # =============================
                subrubro, _ = SUBRUBRO_BASE.objects.get_or_create(
                    id_rubro=rubro,
                    nombre__iexact=subrubro_norm,
                    defaults={
                        'nombre': subrubro_nombre,
                        'descripcion': f'Subrubro {subrubro_nombre}'
                    }
                )

                if subrubro.nombre != subrubro_nombre:
                    subrubro.nombre = subrubro_nombre
                    subrubro.save()

                # =============================
                # 🔹 ARTICULO_BASE
                # =============================
                articulo = ARTICULO_BASE.objects.filter(
                    nombre__iexact=nombre_norm,
                    id_subrubro=subrubro
                ).first()

                if not articulo:
                    articulo = ARTICULO_BASE.objects.create(
                        nombre=nombre,
                        id_subrubro=subrubro,
                        descripcion=f'Artículo {nombre}'
                    )

                # =============================
                # 🔥 🔥 🔥 AREA (DEDUPE)
                # =============================
                try:
                    puntos_json = json.loads(puntos) if isinstance(puntos, str) else puntos
                except Exception:
                    self.stdout.write(self.style.WARNING(f'Error parseando puntos fila {i}'))
                    continue

                area = AREA.objects.filter(
                    coordenadas=puntos_json
                ).first()

                # =============================
                # 🔵 SI NO EXISTE → CREAR
                # =============================
                if not area:
                    area = AREA.objects.create(
                        tipo_area=tipo_area,
                        coordenadas=puntos_json,
                        descripcion=f"{rubro_nombre} / {subrubro_nombre}",
                        color=COLOR_POR_DEFECTO
                    )
                    creados += 1
                else:
                    reutilizados += 1

                # =============================
                # 🔗 RELACIÓN MANY TO MANY
                # =============================
                if not area.id_articulo.filter(id_articulo=articulo.id_articulo).exists():
                    area.id_articulo.add(articulo)
                    relaciones += 1

                # =============================
                # 🔹 LOG PROGRESO
                # =============================
                if i % 100 == 0 or i == total:
                    self.stdout.write(f'Procesados {i}/{total}')

        conn.close()

        # =============================
        # 📊 RESUMEN FINAL
        # =============================
        self.stdout.write(self.style.SUCCESS('--- IMPORTACIÓN FINALIZADA ---'))
        self.stdout.write(f'Áreas creadas: {creados}')
        self.stdout.write(f'Áreas reutilizadas: {reutilizados}')
        self.stdout.write(f'Relaciones creadas: {relaciones}')