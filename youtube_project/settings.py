from pathlib import Path
import os, environ

# Build paths inside the project
BASE_DIR = Path(__file__).resolve().parent.parent

# Inicializar environ
config = environ.Env()
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

# --- SEGURIDAD ---
SECRET_KEY = 'django-insecure-bdhz7!4&n@o!1v2)5x^#dh1xe63gbhi_a0cp98ws!#a9zqdpcr'
DEBUG = True

# Corregido: ALLOWED_HOSTS debe ser una lista limpia
ALLOWED_HOSTS = config.list('ALLOWED_HOSTS', default=['localhost', '127.0.0.1'])

# --- DEFINICIÓN DE APLICACIONES ---
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'videos', # Tu aplicación de videos
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# ¡IMPORTANTE! Cambiado de biblioteca_project a youtube_project
ROOT_URLCONF = 'youtube_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# ¡IMPORTANTE! Cambiado de biblioteca_project a youtube_project
WSGI_APPLICATION = 'youtube_project.wsgi.application'

# --- BASE DE DATOS (MySQL) ---
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST'),
        'PORT': config('DB_PORT'),
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}

# --- VALIDACIÓN DE CONTRASEÑAS ---
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# --- INTERNACIONALIZACIÓN ---
LANGUAGE_CODE = 'es-mx' # Opcional: cambiado a español
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# --- ARCHIVOS ESTÁTICOS ---
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# --- YOUTUBE API KEYS ---
YOUTUBE_API_KEY = config('YOUTUBE_API_KEY')
YOUTUBE_API_SERVICE_NAME = 'youtube'
YOUTUBE_API_VERSION = 'v3'

# --- OAUTH ---
GOOGLE_CLIENT_ID = config('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = config('GOOGLE_CLIENT_SECRET')
GOOGLE_REDIRECT_URI = config('GOOGLE_REDIRECT_URI')

# settings.py
YOUTUBE_SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "openid"
]

# --- CONFIGURACIÓN DE LOGIN ---
LOGIN_URL = 'videos:login'
LOGIN_REDIRECT_URL = 'videos:mis_videos'
LOGOUT_REDIRECT_URL = 'videos:inicio'

# Permitir HTTP para desarrollo local (OAuth)
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'