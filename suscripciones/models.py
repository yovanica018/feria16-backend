from django.db import models
from usuarios.models import UserAPP


class SUSCRIPCIONES(models.Model):
    id_suscripcion = models.AutoField(primary_key=True)
    id_user = models.ForeignKey(UserAPP, on_delete=models.CASCADE)
    tipo = models.CharField(max_length=20)
    fecha_inicio = models.DateTimeField()
    fecha_final = models.DateTimeField()
    estado = models.CharField(max_length=20)
    costo = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.id_user.nombre} - {self.tipo}"