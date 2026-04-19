import json
from mapas.models import AREA

total = 0
modificados = 0
saltados = 0
errores = 0

for area in AREA.objects.all():
    total += 1

    try:
        coords = area.coordenadas

        # Si ya está en formato final
        if isinstance(coords, dict) and "puntos" in coords:
            saltados += 1
            continue

        # Si viene como string JSON
        if isinstance(coords, str):
            puntos_raw = json.loads(coords)

            puntos_limpios = [
                {
                    "lat": p["lat"],
                    "lng": p["lng"]
                }
                for p in puntos_raw
                if "lat" in p and "lng" in p
            ]

            if not puntos_limpios:
                saltados += 1
                continue

            area.coordenadas = {
                "tipo": "polyline",
                "puntos": puntos_limpios
            }

            area.save(update_fields=["coordenadas"])
            modificados += 1
        else:
            saltados += 1

    except Exception as e:
        print(f"Error en AREA ID {area.id}: {e}")
        errores += 1

print("Proceso finalizado")
print(f"Total registros: {total}")
print(f"Modificados: {modificados}")
print(f"Saltados: {saltados}")
print(f"Errores: {errores}")
