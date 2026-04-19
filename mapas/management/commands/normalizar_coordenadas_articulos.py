import json
from django.core.management.base import BaseCommand
from django.db import transaction
from mapas.models import AREA


class Command(BaseCommand):
    help = "Normaliza el campo coordenadas en AREA (Polygon y Polyline)"

    @transaction.atomic
    def handle(self, *args, **options):

        total = 0
        modificados = 0
        saltados = 0
        errores = 0

        self.stdout.write(self.style.WARNING("🚀 Iniciando normalización..."))

        for area in AREA.objects.all():
            total += 1

            try:
                coords = area.coordenadas

                # ==========================================
                # ✅ YA NORMALIZADO CORRECTAMENTE
                # ==========================================
                if (
                    isinstance(coords, dict)
                    and "puntos" in coords
                    and isinstance(coords["puntos"], list)
                ):
                    saltados += 1
                    continue

                # ==========================================
                # 🔄 NORMALIZAR SEGÚN FORMATO
                # ==========================================
                puntos_raw = None

                if isinstance(coords, str):
                    puntos_raw = json.loads(coords)

                elif isinstance(coords, list):
                    puntos_raw = coords

                elif isinstance(coords, dict) and "puntos" in coords:
                    puntos_raw = coords["puntos"]

                else:
                    saltados += 1
                    continue

                if not isinstance(puntos_raw, list):
                    saltados += 1
                    continue

                # ==========================================
                # 🧹 LIMPIAR PUNTOS
                # ==========================================
                puntos_limpios = []

                for p in puntos_raw:
                    if isinstance(p, dict) and "lat" in p and "lng" in p:
                        puntos_limpios.append({
                            "lat": float(p["lat"]),
                            "lng": float(p["lng"])
                        })

                if not puntos_limpios:
                    saltados += 1
                    continue

                # ==========================================
                # 🔥 NORMALIZAR TIPO (CLAVE)
                # ==========================================
                if area.tipo_area == "polygon":
                    tipo_normalizado = "polygon"
                else:
                    tipo_normalizado = "polyline"

                # ==========================================
                # 💾 GUARDAR
                # ==========================================
                area.coordenadas = {
                    "tipo": tipo_normalizado,
                    "puntos": puntos_limpios
                }

                area.save(update_fields=["coordenadas"])
                modificados += 1

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"❌ Error en AREA ID {area.id_area}: {e}")
                )
                errores += 1

        self.stdout.write(self.style.SUCCESS("🎯 Proceso finalizado"))
        self.stdout.write(f"Total registros: {total}")
        self.stdout.write(f"Modificados: {modificados}")
        self.stdout.write(f"Saltados: {saltados}")
        self.stdout.write(f"Errores: {errores}")