from django.urls import path
from . import views

app_name = 'videos'

urlpatterns = [
    # --- Vistas de Navegación ---
    path('', views.inicio, name='inicio'),
    path('mis-videos/', views.mis_videos, name='mis_videos'),
    path('video/<int:video_id>/', views.detalle_video, name='detalle_video'),
    
    # --- Proceso de Subida ---
    path('subir/', views.subir_video, name='subir_video'),
    
    # --- Autenticación y Google OAuth ---
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('autorizar/', views.autorizar_youtube, name='autorizar_youtube'),
    
    # CORRECCIÓN: Ajustamos la ruta para que coincida con lo que Google envía
    # Antes era 'oauth2callback/', ahora es 'youtube/callback/'
    path('youtube/callback/', views.oauth_callback, name='oauth_callback'),
]