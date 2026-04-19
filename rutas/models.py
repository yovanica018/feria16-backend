from django.db import models
from django.core.exceptions import ValidationError
from usuarios.models import UserAPP
from mapas.models import AREA


class HISTORIAL_RUTAS(models.Model):
    id_rutas = models.AutoField(primary_key=True)
    id_user = models.ForeignKey(UserAPP, on_delete=models.CASCADE)
    id_area = models.ForeignKey(AREA, on_delete=models.CASCADE)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('id_user', 'id_area')
        indexes = [
            models.Index(fields=['id_user', 'id_area'])
        ]


    def save(self, *args, **kwargs):
        if self.pk:
            raise ValidationError("El historial no puede editarse.")
        super().save(*args, **kwargs)