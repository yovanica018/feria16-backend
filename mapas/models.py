from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from usuarios.models import UserAPP

from django.contrib.gis.db import models as gis_models
from django.contrib.postgres.indexes import GistIndex


class AREA(models.Model):
    TIPO_AREA = (
        ('Poligono', 'Polígono'),
        ('Polilinea', 'Polilínea'),
    )

    id_area = models.AutoField(primary_key=True)
    id_articulo=models.ManyToManyField('catalogo.ARTICULO_BASE', related_name='areas', blank=True)
    tipo_area = models.CharField(max_length=50, choices=TIPO_AREA)
    coordenadas = models.JSONField()
    geometria = gis_models.GeometryField(srid=4326, null=True, blank=True)
    descripcion = models.TextField()
    color = models.CharField(max_length=7)

    class Meta:
        indexes = [
            GistIndex(fields=['geometria']),
        ]

    def __str__(self):
        return self.descripcion


class AREA_VECINA(models.Model):

    area = models.ForeignKey(
        AREA,
        on_delete=models.CASCADE,
        related_name="vecinos"
    )

    area_vecina = models.ForeignKey(
        AREA,
        on_delete=models.CASCADE,
        related_name="vecino_de"
    )

    class Meta:
        unique_together = ("area", "area_vecina")
        indexes = [
            models.Index(fields=["area"]),
        ]