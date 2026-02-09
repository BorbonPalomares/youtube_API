from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('videos.urls')),  # Incluir rutas de la app videos en la raíz
]

# Configuración para servir archivos estáticos/media en modo DEBUG
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
