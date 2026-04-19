import sqlite3
from collections import defaultdict

from django.core.management.base import BaseCommand

from catalogo.models import RUBRO_BASE, SUBRUBRO_BASE, ARTICULO_BASE


class Command(BaseCommand):
    help = 'Normaliza datos desde SQLite a modelos BASE'

    def handle(self, *args, **kwargs):

        path_db = 'catalogo/management/commands/feria16_exportada.db'

        conn = sqlite3.connect(path_db)
        cursor = conn.cursor()

        # 🔥 ESTRUCTURA LIMPIA EN MEMORIA
        estructura = defaultdict(lambda: defaultdict(set))

        # 🧠 QUERY MAESTRA (JOIN COMPLETO)
        query = """
        SELECT 
            r.Nombre_Rubro,
            sr.Nombre_SubRubro,
            a.Nombre_articulos
        FROM Articulos a
        JOIN Sub_Rubros sr ON a.Id_sub_rubro = sr.Id_sub_rubro
        JOIN Rubros r ON sr.Id_rubro = r.Id_rubro
        """

        cursor.execute(query)
        rows = cursor.fetchall()

        self.stdout.write(f"🔍 Registros leídos: {len(rows)}")

        # 🧱 CONSTRUIR ESTRUCTURA NORMALIZADA
        for rubro, subrubro, articulo in rows:

            if not rubro or not subrubro or not articulo:
                continue

            estructura[rubro][subrubro].add(articulo)

        conn.close()

        # 🚨 LIMPIAR TABLAS DESTINO (opcional pero recomendado en pruebas)
        ARTICULO_BASE.objects.all().delete()
        SUBRUBRO_BASE.objects.all().delete()
        RUBRO_BASE.objects.all().delete()

        total_rubros = 0
        total_subrubros = 0
        total_articulos = 0

        # 🚀 INSERTAR DATOS LIMPIOS
        for nombre_rubro, subrubros in estructura.items():

            rubro_obj = RUBRO_BASE.objects.create(
                nombre=nombre_rubro
            )
            total_rubros += 1

            for nombre_subrubro, articulos in subrubros.items():

                subrubro_obj = SUBRUBRO_BASE.objects.create(
                    id_rubro=rubro_obj,
                    nombre=nombre_subrubro
                )
                total_subrubros += 1

                for nombre_articulo in articulos:

                    ARTICULO_BASE.objects.create(
                        id_subrubro=subrubro_obj,
                        nombre=nombre_articulo
                    )
                    total_articulos += 1

        self.stdout.write(self.style.SUCCESS("✅ NORMALIZACIÓN COMPLETA"))
        self.stdout.write(f"Rubros: {total_rubros}")
        self.stdout.write(f"Subrubros: {total_subrubros}")
        self.stdout.write(f"Artículos: {total_articulos}")