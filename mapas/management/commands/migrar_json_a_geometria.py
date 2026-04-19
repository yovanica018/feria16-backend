import json
from django.core.management.base import BaseCommand
from django.contrib.gis.geos import Polygon, LineString
from django.db import transaction
from mapas.models import AREA


class Command(BaseCommand):
    help = "Convierte coordenadas JSON a GeometryField (PostGIS)"

    def handle(self, *args, **options):
        self.stdout.write("🚀 Iniciando migración JSON → Geometría")

        areas = AREA.objects.filter(
            geometria__isnull=True,
            coordenadas__isnull=False
        )

        total = areas.count()
        self.stdout.write(f"Áreas a procesar: {total}")

        with transaction.atomic():
            for i, area in enumerate(areas, start=1):

                coords_json = area.coordenadas

                # Si viene como string
                if isinstance(coords_json, str):
                    try:
                        coords_json = json.loads(coords_json)
                    except json.JSONDecodeError:
                        self.stdout.write(
                            f"❌ Área {area.id_area} tiene JSON inválido"
                        )
                        continue

                if not isinstance(coords_json, dict):
                    continue

                puntos_json = coords_json.get("puntos", [])

                if not puntos_json or len(puntos_json) < 2:
                    self.stdout.write(
                        f"⚠ Área {area.id_area} sin suficientes puntos"
                    )
                    continue

                puntos = []

                for punto in puntos_json:
                    lat = punto.get("lat")
                    lng = punto.get("lng")

                    if lat is None or lng is None:
                        continue

                    # IMPORTANTE: siempre (lng, lat)
                    puntos.append((lng, lat))

                if len(puntos) < 2:
                    continue

                try:
                    if area.tipo_area == "polygon":

                        # Un polígono necesita mínimo 3 puntos
                        if len(puntos) < 3:
                            continue

                        # cerrar el polígono si no está cerrado
                        if puntos[0] != puntos[-1]:
                            puntos.append(puntos[0])

                        geometria = Polygon(puntos, srid=4326)

                    else:
                        geometria = LineString(puntos, srid=4326)

                    area.geometria = geometria
                    area.save(update_fields=["geometria"])

                except Exception as e:
                    self.stdout.write(
                        f"❌ Error en área {area.id_area}: {str(e)}"
                    )

                if i % 50 == 0 or i == total:
                    self.stdout.write(f"Procesados {i}/{total}")

        self.stdout.write(self.style.SUCCESS("🎉 Migración completada"))