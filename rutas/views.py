import json
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from .models import HISTORIAL_RUTAS
from mapas.models import AREA
from usuarios.models import UserAPP
from django.views.decorators.http import require_GET
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
@require_POST
def toggle_area_favorita(request):

    try:
        data = json.loads(request.body)

        user_id = data.get("user_id")
        area_id = data.get("area_id")

    except Exception:
        return JsonResponse({"error": "JSON inválido"}, status=400)

    if not user_id or not area_id:
        return JsonResponse({"error": "Datos incompletos"}, status=400)

    try:
        user = UserAPP.objects.get(pk=user_id)
        area = AREA.objects.get(pk=area_id)
    except (UserAPP.DoesNotExist, AREA.DoesNotExist):
        return JsonResponse({"error": "Usuario o área no encontrada"}, status=404)

    favorito = HISTORIAL_RUTAS.objects.filter(
        id_user=user,
        id_area=area
    ).first()

    if favorito:
        favorito.delete()
        return JsonResponse({
            "favorito": False,
            "message": "Área eliminada de favoritos"
        })

    HISTORIAL_RUTAS.objects.create(
        id_user=user,
        id_area=area,
        fecha=timezone.now()
    )

    return JsonResponse({
        "favorito": True,
        "message": "Área guardada en favoritos"
    })

@require_GET
def area_es_favorita(request):
    user_id = request.GET.get("user_id")

    if not user_id:
        return JsonResponse({"error": "user_id requerido"}, status=400)

    favoritos = list(
        HISTORIAL_RUTAS.objects
        .filter(id_user_id=user_id)
        .values_list("id_area_id", flat=True)
    )

    return JsonResponse({
        "areas": favoritos
    })
