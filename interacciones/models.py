from django.db import models
from usuarios.models import UserAPP
from django.core.exceptions import ValidationError


class CALIFICACIONES(models.Model):
    TIPO_CHOICES = (
        ('positivo', 'Positivo'),
        ('negativo', 'Negativo'),
    )

    id_calificacion = models.AutoField(primary_key=True)

    # usuario visitante
    id_user = models.ForeignKey(UserAPP,related_name='calificaciones_realizadas',on_delete=models.CASCADE)

    # comerciante o tienda
    id_user_vendedor = models.ForeignKey(UserAPP,related_name='calificaciones_recibidas',on_delete=models.CASCADE)

    tipo_calificacion = models.CharField(max_length=10,choices=TIPO_CHOICES)

    comentario = models.TextField(blank=True, null=True)

    fecha = models.DateTimeField(auto_now_add=True)

    def clean(self):
        # solo visitantes califican
        if self.id_user.rol != 'visitante':
            raise ValidationError(
                "Solo usuarios visitantes pueden calificar."
            )

        # no auto calificarse
        if self.id_user == self.id_user_vendedor:
            raise ValidationError(
                "No puedes calificarte a ti mismo."
            )

        # solo comerciante o tienda recibe
        if self.id_user_vendedor.rol not in ['comerciante', 'tienda']:
            raise ValidationError(
                "Solo comerciantes o tiendas pueden recibir calificación."
            )

    def __str__(self):
        return f"{self.id_user} → {self.id_user_vendedor} ({self.tipo_calificacion})"

    class Meta:
        unique_together = ('id_user', 'id_user_vendedor')


class BUSQUEDAS(models.Model):
    id_busqueda = models.AutoField(primary_key=True)
    id_user = models.ForeignKey(UserAPP, on_delete=models.CASCADE)
    texto_busqueda = models.CharField(max_length=255)
    fecha = models.DateTimeField()
    num_resultados = models.IntegerField()

    def save(self, *args, **kwargs):
        if self.pk:
            raise ValidationError("Las búsquedas no pueden modificarse.")
        super().save(*args, **kwargs)