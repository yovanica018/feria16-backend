from django.db import models
from usuarios.models import UserAPP
from catalogo.models import ARTICULO_BASE, RUBRO_BASE, SUBRUBRO_BASE
from django.core.exceptions import ValidationError


class ARTICULOS_VENTA(models.Model):
    ESTADO_CHOICES = (
        ('activo', 'Activo'),
        ('pausado', 'Pausado'),
        ('agotado', 'Agotado'),
        ('eliminado', 'Eliminado lógico'),
    )

    id_venta = models.AutoField(primary_key=True)
    id_user = models.ForeignKey(UserAPP, on_delete=models.CASCADE)

    id_articulo = models.ForeignKey(ARTICULO_BASE,on_delete=models.CASCADE,related_name='ventas',null=True,blank=True)

    descripcion = models.TextField()
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    fecha = models.DateTimeField()
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES)

    def clean(self):
        if self.precio <= 0:
            raise ValidationError("Precio inválido.")

        if self.id_user.estado != 'activo':
            raise ValidationError("Usuario inactivo no puede publicar.")

        if not hasattr(self.id_user, 'negocio'):
            raise ValidationError("Debe registrar un negocio antes de publicar.")

    def __str__(self):
        return f"{self.id_articulo.nombre} - {self.id_user.nombre}"

    class Meta:
        indexes = [
            models.Index(fields=['estado']),
            models.Index(fields=['id_articulo']),
            models.Index(fields=['id_user']),
        ]



class GALERIA(models.Model):
    id_galeria = models.AutoField(primary_key=True)
    id_venta = models.ForeignKey(ARTICULOS_VENTA, on_delete=models.CASCADE)
    tipo = models.CharField(max_length=20)
    url = models.URLField()
    descripcion = models.CharField(max_length=255)

    def __str__(self):
        return f"Galería {self.id_venta.nombre}"


class OFERTAS(models.Model):
    id_oferta = models.AutoField(primary_key=True)
    id_venta = models.ForeignKey(ARTICULOS_VENTA, on_delete=models.CASCADE)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    imagen = models.URLField()
    fecha_inicio = models.DateTimeField()
    fecha_final = models.DateTimeField()
    estado = models.CharField(max_length=20)

    def __str__(self):
        return f"Oferta {self.id_venta.nombre}"