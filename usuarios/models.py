from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.contrib.gis.db import models as gis_models

class UsuarioManager(BaseUserManager):
    def create_user(self, email, nombre, password=None, **extra_fields):
        if not email:
            raise ValueError("El usuario debe tener un correo electrónico")
        email = self.normalize_email(email)
        user = self.model(email=email, nombre=nombre, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, nombre, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, nombre, password, **extra_fields)


class Usuario(AbstractBaseUser, PermissionsMixin):
    firebase_uid = models.CharField(max_length=128, unique=True, null=True, blank=True)
    email = models.EmailField(unique=True)
    nombre = models.CharField(max_length=100)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    tipo_usuario = models.CharField(
    max_length=20,
    choices=[
        ('comprador', 'Comprador'),
        ('comerciante', 'Comerciante'),
        ('promotor', 'Promotor'),
        ('admin', 'Administrador'),
        ],
        default='comprador'
    )
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(default=timezone.now)

    objects = UsuarioManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nombre']

    def __str__(self):
        return self.email

# ✅ Agregamos esta propiedad para compatibilidad con Django
    @property
    def username(self):
        return self.email

class UserAPP(models.Model):

    id_user = models.AutoField(primary_key=True)
    codigo_user = models.CharField(max_length=20,unique=True)
    UID = models.CharField(max_length=255, unique=True, null=False, blank=False)
    email = models.EmailField(max_length=255, null=True, blank=True)
    proveedor = models.CharField(
        max_length=50,
        choices=[
            ('google', 'Google'),
            ('email', 'Correo Electrónico'),
            ('telefono', 'Teléfono'),
        ],
        default='google'
    )
    nombre = models.CharField(max_length=255, null=True, blank=True)
    imagen = models.URLField(max_length=500, null=True, blank=True)
    rol = models.CharField(max_length=50, default='visitante')
    telefono = models.CharField(max_length=20, null=True, blank=True)
    ultimo_inicio = models.DateTimeField(default=timezone.now)
    estado = models.CharField(max_length=10, default='activo')

    @property
    def is_authenticated(self):
        return True

    def __str__(self):
        return f"{self.nombre or 'Sin nombre'} ({self.proveedor})"

    def save(self, *args, **kwargs):
        is_new = self.pk is None

        super().save(*args, **kwargs)  # primero guarda para obtener ID

        if is_new and not self.codigo_user:
            self.codigo_user = f"USER-{10000 + self.id_user}"
            super().save(update_fields=["codigo_user"])

class UBICACIONES(models.Model):
    TIPO_CHOICES = (
        ('fija', 'Fija'),
        ('movil', 'Móvil'),
    )

    id_ubicacion = models.AutoField(primary_key=True)
    id_user = models.ForeignKey(UserAPP, on_delete=models.CASCADE,related_name='ubicaciones')
    latitud = models.DecimalField(max_digits=9, decimal_places=6)
    longitud = models.DecimalField(max_digits=9, decimal_places=6)
    geometria_user = gis_models.GeometryField(srid=4326, null=True, blank=True)
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    def clean(self):
        # 🔒 Usuario activo
        if self.id_user.estado != 'activo':
            raise ValidationError("Usuario inactivo no puede registrar ubicación.")

        # 📍 Validación geográfica
        if not (-90 <= self.latitud <= 90):
            raise ValidationError("Latitud fuera de rango.")
        if not (-180 <= self.longitud <= 180):
            raise ValidationError("Longitud fuera de rango.")

        # 🧱 Fija: una actualización por día
        if self.tipo == 'fija':
            hoy = timezone.now().date()
            existe = UBICACIONES.objects.filter(
                id_user=self.id_user,
                tipo='fija',
                fecha_actualizacion__date=hoy
            ).exclude(pk=self.pk).exists()

            if existe:
                raise ValidationError("Ubicación fija solo puede actualizarse una vez por día.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.id_user.nombre} - {self.tipo}"

    class Meta:
        indexes = [
            models.Index(fields=['id_user']),
            models.Index(fields=['latitud', 'longitud']),
        ]