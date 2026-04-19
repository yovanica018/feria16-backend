from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from .models import UserAPP
from django.shortcuts import render
from firebase_admin import auth as firebase_auth

from django.views.decorators.csrf import csrf_exempt

# 2. Decoradores y Clases de DRF

from rest_framework.permissions import AllowAny              # <-- Importación de AllowAny


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def perfil_usuario(request):
    usuario = request.user
    return Response({
        "id": usuario.id,
        "email": usuario.email,
        "nombre": usuario.nombre,
        "telefono": usuario.telefono,
        "tipo_usuario": usuario.tipo_usuario,
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def registrar_user_app(request):

    data = request.data
    UID = data.get('UID')

    if not UID:
        return Response({"success": False, "error": "UID es obligatorio"}, status=400)

    proveedor = (data.get('proveedor') or 'google').lower()

    if proveedor not in ['google', 'email', 'telefono']:
        return Response({"success": False, "error": "Proveedor inválido"}, status=400)

    user, created = UserAPP.objects.update_or_create(
        UID=UID,
        defaults={
            "email": data.get("email"),
            "proveedor": proveedor,
            "nombre": data.get("nombre"),
            "imagen": data.get("imagen"),
            "telefono": data.get("telefono"),

            "ultimo_inicio": timezone.now(),
            "estado": "activo"
        }
    )

    return Response({
        "success": True,
        "created": created,
        "user": {
            "id_user": user.id_user,
            "UID": user.UID,
            "email": user.email,
            "proveedor": user.proveedor,
            "nombre": user.nombre,
            "imagen": user.imagen,
            "telefono": user.telefono,
            "rol": user.rol,
            "ultimo_inicio": user.ultimo_inicio,
            "estado": user.estado,
        }
    }, status=200)



@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def verify_firebase_user(request):

    id_token = request.headers.get('Authorization', '').replace('Bearer ', '').strip()

    if not id_token:
        return Response({"detail": "Token no proporcionado"}, status=400)

    try:
        decoded = firebase_auth.verify_id_token(id_token, clock_skew_seconds=30)
        uid = decoded.get("uid")
        print(f"✅ Token válido para UID {uid}")

    except Exception as e:
        print("❌ Token inválido:", e)
        return Response({"detail": "Token inválido", "error": str(e)}, status=401)

    try:
        user = UserAPP.objects.get(UID=uid)

        # ✅ Verificar si está activo
        if user.estado != "activo":
            return Response({
                "success": False,
                "detail": "El usuario está inactivo. Contacte al administrador.",
                "estado": user.estado
            }, status=403)

        return Response({
            "success": True,
            "user": {
                "id_user": user.id_user,
                "UID": user.UID,
                "email": user.email,
                "nombre": user.nombre,
                "rol": user.rol,
            }
        }, status=200)

    except UserAPP.DoesNotExist:
        return Response({"success": False, "detail": "Usuario no registrado"}, status=404)


@api_view(['POST'])
@permission_classes([AllowAny])
def logout_user(request):
    UID = request.data.get("UID")

    if not UID:
        return Response({"error": "UID requerido"}, status=400)

    try:

        user = UserAPP.objects.get(UID=UID)

        user.estado = "inactivo"
        user.ultimo_inicio = timezone.now()
        user.save()

        return Response({"success": True})
    except UserAPP.DoesNotExist:
        return Response({"error": "Usuario no encontrado"}, status=404)