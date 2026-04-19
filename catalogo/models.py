from django.db import models
from mapas.models import AREA
from django.contrib.postgres.search import SearchVectorField
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVector

class RUBRO_BASE(models.Model):
    id_rubro = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)

    class Meta:
        ordering = ['nombre']
        indexes = [
            models.Index(fields=['nombre']),
        ]

    def __str__(self):
        return self.nombre


class SUBRUBRO_BASE(models.Model):
    id_subrubro = models.AutoField(primary_key=True)
    id_rubro = models.ForeignKey(
        RUBRO_BASE,
        on_delete=models.CASCADE,
        related_name='subrubros'
    )
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)

    class Meta:
        unique_together = ('id_rubro', 'nombre')
        ordering = ['nombre']
        indexes = [
            models.Index(fields=['nombre']),
        ]

    def __str__(self):
        return self.nombre


class ARTICULO_BASE(models.Model):
    id_articulo = models.AutoField(primary_key=True)
    id_subrubro = models.ForeignKey(
        SUBRUBRO_BASE,
        on_delete=models.CASCADE,
        related_name='articulos_base'
    )
    nombre = models.CharField(max_length=255)
    descripcion = models.TextField(blank=True)
    search_vector = SearchVectorField(null=True)

    class Meta:
        unique_together = ('id_subrubro', 'nombre')
        ordering = ['nombre']
        indexes = [
            models.Index(fields=['nombre']),
            GinIndex(fields=['search_vector']),
        ]

    def __str__(self):
        return self.nombre

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        ARTICULO_BASE.objects.filter(pk=self.pk).update(
            search_vector=(
                    SearchVector('nombre', weight='A') +
                    SearchVector('descripcion', weight='B')
            )
        )
