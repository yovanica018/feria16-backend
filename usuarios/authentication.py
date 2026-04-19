import firebase_admin
from firebase_admin import auth as firebase_auth

from rest_framework import authentication, exceptions


from usuarios.models import UserAPP


class FirebaseAuthentication(authentication.BaseAuthentication):
    """
    Autenticador JWT Firebase para usuarios móviles.
    """

    def authenticate(self, request):
        auth_header = request.headers.get("Authorization")

        if not auth_header:
            return None

        parts = auth_header.split()

        if len(parts) != 2 or parts[0].lower() != "bearer":
            raise exceptions.AuthenticationFailed(
                "Encabezado Authorization inválido"
            )

        id_token = parts[1]

        try:
            decoded_token = firebase_auth.verify_id_token(
                id_token
            )
        except Exception:
            raise exceptions.AuthenticationFailed(
                "Token inválido o expirado"
            )

        uid = decoded_token.get("uid")
        email = decoded_token.get("email")
        nombre = decoded_token.get(
            "name",
            "Usuario Firebase"
        )

        try:
            usuario = UserAPP.objects.get(
                UID=uid,
                estado="activo"
            )
        except UserAPP.DoesNotExist:
            raise exceptions.AuthenticationFailed(
                "Usuario no registrado en la app"
            )

        return (usuario, None)
