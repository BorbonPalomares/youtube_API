import os
import time
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout, login
from django.core.files.storage import FileSystemStorage
from django.db.models import Sum
from django.core.paginator import Paginator

from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials

# Asumiendo que estos archivos existen en tu carpeta de app
from .models import Video
from .youtube_service import YouTubeService
from .upload_service import YouTubeUploadService

# Definimos las categorías aquí para pasarlas al Template HTML
YOUTUBE_CATEGORIES = [
    ('22', 'People & Blogs'),
    ('27', 'Education'),
    ('28', 'Programación'),
    ('10', 'Music'),
    ('17', 'Sports'),
    ('20', 'Gaming'),
]

# --- VISTAS GENERALES ---

def inicio(request):
    videos = Video.objects.all().order_by('-fecha_publicacion')
    total_videos = videos.count()
    total_views = videos.aggregate(Sum('vistas'))['vistas__sum'] or 0
    total_likes = videos.aggregate(Sum('likes'))['likes__sum'] or 0
    
    context = {
        'videos': videos,
        'total_videos': total_videos,
        'total_views': total_views,
        'total_likes': total_likes,
    }
    return render(request, 'videos/inicio.html', context)

@login_required
def mis_videos(request):
    videos_list = Video.objects.filter(agregado_por=request.user).order_by('-fecha_publicacion')

    # Buscador
    query = request.GET.get('buscar')
    if query:
        videos_list = videos_list.filter(titulo__icontains=query)

    # Filtro Categoría
    categoria_filtro = request.GET.get('categoria')
    if categoria_filtro:
        videos_list = videos_list.filter(categoria=categoria_filtro)

    # Cálculos
    total_views = videos_list.aggregate(Sum('vistas'))['vistas__sum'] or 0
    total_likes = videos_list.aggregate(Sum('likes'))['likes__sum'] or 0
    total_comments = videos_list.aggregate(Sum('comentarios'))['comentarios__sum'] or 0
    cantidad_videos = videos_list.count()

    # Paginación
    paginator = Paginator(videos_list, 10) 
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'videos': page_obj,
        'total_views': total_views,
        'total_likes': total_likes,
        'total_comments': total_comments,
        'total_videos_count': cantidad_videos
    }
    return render(request, 'videos/mis_videos.html', context)

def detalle_video(request, video_id):
    video = get_object_or_404(Video, pk=video_id)
    return render(request, 'videos/detalle_video.html', {'video': video})

def logout_view(request):
    logout(request)
    messages.info(request, "Sesión cerrada.")
    return redirect('videos:inicio')

def login_view(request):
    if request.user.is_authenticated:
        return redirect('videos:mis_videos')
    return render(request, 'videos/login.html')

# --- OAUTH & UPLOAD LOGIC ---

def autorizar_youtube(request):
    """Paso 1: Iniciar el flujo OAuth con acceso offline forzado"""
    try:
        # Creamos el flow manualmente para asegurar el control total de los parámetros
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "redirect_uris": [settings.GOOGLE_REDIRECT_URI],
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token"
                }
            },
            scopes=settings.YOUTUBE_SCOPES
        )
        flow.redirect_uri = settings.GOOGLE_REDIRECT_URI

        # access_type='offline' permite obtener el refresh_token
        # prompt='consent' obliga a Google a pedir permiso y entregar el refresh_token de nuevo
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            prompt='consent',
            include_granted_scopes='true'
        )

        request.session['oauth_state'] = state
        return redirect(authorization_url)
    except Exception as e:
        messages.error(request, f"Error al conectar con Google: {e}")
        return redirect('videos:login')

def oauth_callback(request):
    """Paso 2: Callback de Google"""
    state = request.session.get('oauth_state')
    if not state:
        messages.error(request, "Error de seguridad (State missing).")
        return redirect('videos:inicio')

    try:
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "redirect_uris": [settings.GOOGLE_REDIRECT_URI],
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token"
                }
            },
            scopes=settings.YOUTUBE_SCOPES,
            state=state
        )
        flow.redirect_uri = settings.GOOGLE_REDIRECT_URI
        flow.fetch_token(authorization_response=request.build_absolute_uri())
        credentials = flow.credentials

        # Información de perfil
        session = flow.authorized_session()
        profile_info = session.get('https://www.googleapis.com/oauth2/v2/userinfo').json()
        email = profile_info.get('email')
        nombre = profile_info.get('given_name', 'Usuario')

        if email:
            user, created = User.objects.get_or_create(username=email)
            if created:
                user.email = email
                user.first_name = nombre
                user.save()

            login(request, user, backend='django.contrib.auth.backends.ModelBackend')

            # Guardar credenciales de forma explícita para evitar errores de campos faltantes
            request.session['credentials'] = {
                'token': credentials.token,
                'refresh_token': credentials.refresh_token,
                'token_uri': credentials.token_uri,
                'client_id': credentials.client_id,
                'client_secret': credentials.client_secret,
                'scopes': credentials.scopes
            }
            # Importante para asegurar que la sesión se guarde
            request.session.modified = True
            
            messages.success(request, f"¡Bienvenido, {nombre}!")
            return redirect('videos:mis_videos')
    except Exception as e:
        messages.error(request, f"Error en autenticación: {e}")
    return redirect('videos:inicio')

@login_required
def subir_video(request):
    """Paso 3: Formulario y proceso de subida"""
    creds_data = request.session.get('credentials')
    
    if not creds_data or not creds_data.get('refresh_token'):
        messages.info(request, "Tu sesión de YouTube no permite renovar el acceso. Por favor, autoriza de nuevo.")
        return redirect('videos:autorizar_youtube')

    if request.method == 'POST':
        archivo = request.FILES.get('video')
        uploaded_file_path = None
        
        if archivo:
            try:
                # 1. Guardar temporalmente
                fs = FileSystemStorage()
                filename = fs.save(f"temp_{request.user.id}_{archivo.name}", archivo)
                uploaded_file_path = fs.path(filename)

                # 2. Reconstruir credenciales para que puedan auto-refrescarse
                credentials = Credentials(
                    token=creds_data['token'],
                    refresh_token=creds_data['refresh_token'],
                    token_uri=creds_data['token_uri'],
                    client_id=creds_data['client_id'],
                    client_secret=creds_data['client_secret'],
                    scopes=creds_data['scopes']
                )

                # 3. Subida
                uploader = YouTubeUploadService()
                response = uploader.subir_video(
                    credentials=credentials,
                    archivo_path=uploaded_file_path,
                    titulo=request.POST.get('titulo'),
                    descripcion=request.POST.get('descripcion'),
                    categoria=request.POST.get('categoria'),
                    privacidad=request.POST.get('privacidad')
                )

                if 'id' in response:
                    # Guardar en DB local
                    snippet = response.get('snippet', {})
                    thumbs = snippet.get('thumbnails', {})
                    high_thumb = thumbs.get('high', {}).get('url') or thumbs.get('default', {}).get('url')

                    Video.objects.create(
                        youtube_id=response['id'],
                        titulo=snippet.get('title', request.POST.get('titulo')),
                        descripcion=snippet.get('description', request.POST.get('descripcion')),
                        url_video=f"https://www.youtube.com/watch?v={response['id']}",
                        url_thumbnail=high_thumb,
                        canal_nombre=snippet.get('channelTitle', ''),
                        fecha_publicacion=snippet.get('publishedAt'),
                        categoria=request.POST.get('categoria'),
                        agregado_por=request.user
                    )
                    messages.success(request, "¡Video subido con éxito!")
                    return redirect('videos:mis_videos')
                else:
                    messages.error(request, "Error: YouTube no generó un ID de video.")

            except Exception as e:
                # Si el error es de tokens, limpiar sesión para forzar re-login
                if "refresh_token" in str(e).lower():
                    if 'credentials' in request.session: del request.session['credentials']
                messages.error(request, f"Error crítico: {e}")
            
            finally:
                # BORRADO SEGURO PARA WINDOWS
                if uploaded_file_path and os.path.exists(uploaded_file_path):
                    try:
                        time.sleep(1.0)
                        os.remove(uploaded_file_path)
                    except PermissionError:
                        pass
        else:
            messages.error(request, "Selecciona un archivo.")

    return render(request, 'videos/subir_video.html', {'categorias': YOUTUBE_CATEGORIES})