from django.contrib import admin
from django.urls import path
from django.http import HttpResponse  # 👈 importamos esto
from usuarios.views import registrar_user_app, verify_firebase_user, logout_user
from mapas.views import AreaListAPIView, AreaFeriaAPIView,VerificarUbicacionFeriaAPIView,AreasPorArticuloAPIView,AreaGeometryAPIView,DetalleArea
from rutas.views import toggle_area_favorita, area_es_favorita
from catalogo.views import ArticuloSearchView
from ventas.views import ComerciantesPorArticuloAPIView,TiendasPorArticuloAPIView,DetalleVendedorAPIView
from interacciones.views import CalificarVendedorAPIView,ObtenerCalificacionVendedorAPIView

print("✅ Cargando rutas de feria_api/urls.py")

# 👇 Vista simple de prueba
def home(request):
    return HttpResponse("🚀 Backend Feria API funcionando correctamente")

urlpatterns = [
    path('', home, name='home'),  # 👈 Ruta raíz agregada
    path('admin/', admin.site.urls),
    path('api/registrar_user_app/', registrar_user_app, name='registrar_user_app'),
    path('api/auth/firebase/verify/', verify_firebase_user, name='verify_firebase_user'),
    path("api/usuario/logout/", logout_user, name='logout_user'),
    path('api/mapas/areas/', AreaListAPIView.as_view(), name='mapas_areas'),
    path('api/articulos/', ArticuloSearchView.as_view(), name='buscar-articulos'),
    path('api/mapas/area-feria/', AreaFeriaAPIView.as_view(), name='mapa_feria'),
    path('api/mapas/verificar-ubicacion/',VerificarUbicacionFeriaAPIView.as_view(),name='verificar_ubicacion_feria'),
    path('api/mapas/areas-por-articulo/', AreasPorArticuloAPIView.as_view(),name='areas_por_articulo'),
    path("api/mapas/area/<int:id_area>/",AreaGeometryAPIView.as_view(),name="area-geometry"),

    path('api/toggle-area-favorita/', toggle_area_favorita),
    path('api/area-es-favorita/', area_es_favorita),
    path('api/detalle-area/', DetalleArea),

    path("api/ventas/comerciantes-por-articulo/",ComerciantesPorArticuloAPIView.as_view(),name="comerciantes-por-articulo"),
    path("api/ventas/tiendas-por-articulo/",TiendasPorArticuloAPIView.as_view(),name="tiendas-por-articulo"),

    path('api/ventas/detalle-vendedor/',DetalleVendedorAPIView.as_view(),name='detalle-vendedor'),
    path("api/interacciones/calificar-vendedor/",CalificarVendedorAPIView.as_view(),name="calificar-vendedor"),
    path("api/interacciones/obtener-calificacion/",ObtenerCalificacionVendedorAPIView.as_view(),name="obtener-calificacion"),

]

