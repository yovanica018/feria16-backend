from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404

from usuarios.models import UserAPP
from interacciones.models import CALIFICACIONES


class CalificarVendedorAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):

        usuario = request.user

        # 🔴 VALIDAR ROL
        if usuario.rol != "visitante":
            return Response(
                {"error": "Solo los visitantes pueden calificar"},
                status=status.HTTP_403_FORBIDDEN
            )

        id_user_vendedor = request.data.get("id_user_vendedor")
        tipo_calificacion = request.data.get("tipo_calificacion")

        if tipo_calificacion not in ["positivo", "negativo"]:
            return Response(
                {"error": "tipo_calificacion inválido"},
                status=status.HTTP_400_BAD_REQUEST
            )

        vendedor = get_object_or_404(
            UserAPP,
            id_user=id_user_vendedor,
            estado="activo"
        )

        # 🔴 EVITAR AUTOCALIFICACIÓN
        if usuario.id_user == vendedor.id_user:
            return Response(
                {"error": "No puedes calificarte a ti mismo"},
                status=status.HTTP_400_BAD_REQUEST
            )

        calificacion, creada = CALIFICACIONES.objects.update_or_create(
            id_user=usuario,
            id_user_vendedor=vendedor,
            defaults={
                "tipo_calificacion": tipo_calificacion
            }
        )

        return Response({
            "success": True,
            "accion": "creada" if creada else "actualizada",
            "tipo_calificacion": calificacion.tipo_calificacion
        })


class ObtenerCalificacionVendedorAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        usuario_visitante = request.user

        id_user_vendedor = request.query_params.get(
            "id_user_vendedor"
        )

        if not id_user_vendedor:
            return Response(
                {
                    "error": "id_user_vendedor es requerido"
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            vendedor = UserAPP.objects.get(
                id_user=id_user_vendedor,
                estado="activo"
            )
        except UserAPP.DoesNotExist:
            return Response(
                {
                    "error": "Comerciante no encontrado"
                },
                status=status.HTTP_404_NOT_FOUND
            )

        calificacion = CALIFICACIONES.objects.filter(
            id_user=usuario_visitante,
            id_user_vendedor=vendedor
        ).first()

        if not calificacion:
            return Response(
                {
                    "calificado": False,
                    "tipo_calificacion": None
                },
                status=status.HTTP_200_OK
            )

        return Response(
            {
                "calificado": True,
                "tipo_calificacion": calificacion.tipo_calificacion
            },
            status=status.HTTP_200_OK
        )