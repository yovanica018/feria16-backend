from django.db import models
from django.core.exceptions import ValidationError
from usuarios.models import UserAPP


class NEGOCIO(models.Model):
    id_negocio = models.AutoField(primary_key=True)
    id_user = models.OneToOneField(UserAPP, on_delete=models.CASCADE,related_name='negocio')
    nombre_negocio = models.CharField(max_length=100)
    descripcion = models.TextField()

    def clean(self):
        if self.id_user.rol not in ['comerciante', 'tienda']:
            raise ValidationError("Solo comerciantes o tiendas pueden tener un negocio.")

    def __str__(self):
        return self.nombre_negocio

    class Meta:
        indexes = [
            models.Index(fields=['id_user']),
        ]

