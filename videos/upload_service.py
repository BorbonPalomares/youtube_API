import os
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request  # Añadido para refresco automático
from django.conf import settings

class YouTubeUploadService:
    """Servicio para subir videos a YouTube con OAuth"""
    
    def obtener_url_autorizacion(self):
        """Genera URL para que usuario autorice la app"""
        
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
        
        # access_type='offline' es vital para obtener el refresh_token
        # prompt='consent' obliga a Google a entregar el refresh_token aunque ya se haya autorizado antes
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent' 
        )
        
        return authorization_url, state
    
    def subir_video(self, credentials, archivo_path, titulo, descripcion, categoria='22', privacidad='private'):
        """
        Sube un video a YouTube de forma fragmentada y maneja el refresco de tokens.
        """
        
        # --- MEJORA CRÍTICA: Refresco automático del token ---
        # Si el access_token caducó pero tenemos el refresh_token, esto lo renueva silenciosamente
        if not credentials.valid:
            if credentials.expired and credentials.refresh_token:
                try:
                    credentials.refresh(Request())
                except Exception as e:
                    raise Exception(f"No se pudo refrescar el token: {str(e)}")

        # Construye el servicio de la API de YouTube
        youtube = build('youtube', 'v3', credentials=credentials)
        
        # Metadatos del video
        body = {
            'snippet': {
                'title': titulo,
                'description': descripcion,
                'categoryId': categoria
            },
            'status': {
                'privacyStatus': privacidad,
                'selfDeclaredMadeForKids': False,
            }
        }
        
        # Preparar el archivo para la subida resumable
        media = MediaFileUpload(
            archivo_path,
            mimetype='video/*',
            chunksize=1024*1024, # 1MB por fragmento
            resumable=True
        )
        
        try:
            request = youtube.videos().insert(
                part='snippet,status',
                body=body,
                media_body=media
            )
            
            # Ejecutar la subida por fragmentos (chunks)
            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    print(f"Progreso de subida: {int(status.progress() * 100)}%")
            
            return response
            
        except Exception as e:
            raise Exception(f"Error en la API de YouTube: {str(e)}")