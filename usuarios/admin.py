from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario, UserAPP, UBICACIONES


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    model = Usuario
    list_display = ('email', 'nombre', 'get_tipo_usuario', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_active',)
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Información personal', {'fields': ('nombre', 'telefono', 'tipo_usuario')}),
        ('Permisos', {'fields': ('is_staff', 'is_active', 'is_superuser', 'groups', 'user_permissions')}),
        ('Fechas importantes', {'fields': ('last_login', 'fecha_creacion')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'nombre', 'password1', 'password2', 'is_staff', 'is_active')}
        ),
    )
    search_fields = ('email',)
    ordering = ('email',)

    # ✅ Método auxiliar para mostrar tipo_usuario en el panel admin
    def get_tipo_usuario(self, obj):
        return obj.tipo_usuario
    get_tipo_usuario.short_description = 'Tipo de Usuario'


@admin.register(UserAPP)
class UserAPPAdmin(admin.ModelAdmin):
    list_display = ('id_user', 'nombre', 'email', 'proveedor', 'rol', 'ultimo_inicio')
    search_fields = ('email', 'nombre')
    list_filter = ('proveedor', 'rol')


@admin.register(UBICACIONES)
class UbicacionesAdmin(admin.ModelAdmin):
    list_display = ('id_ubicacion', 'id_user', 'tipo', 'fecha_actualizacion')


