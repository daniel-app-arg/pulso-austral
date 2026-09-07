"""
Django settings for config project (backend de Pulso Austral).

Reemplaza a Supabase como fuente de datos del dashboard. Lectura pública sin
autenticación (equivalente a las políticas RLS del esquema original);
escritura reservada al staff (Django admin) o a comandos de management
corridos desde el backend (equivalente a la "service_role key").
"""

from pathlib import Path

from decouple import Csv, config as env
import dj_database_url

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET_KEY', default='django-insecure-ox=(h+9anhu(f@9j%xr_i9#7sr9$feq@w^$_+oa1*6724u&6dj')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env('DEBUG', default=True, cast=bool)

ALLOWED_HOSTS = env('ALLOWED_HOSTS', default='localhost,127.0.0.1', cast=Csv())


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'rest_framework',
    'django_filters',
    'corsheaders',

    'indicadores',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # sirve /static/ (admin) sin depender de nginx
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'config.wsgi.application'


# Database
# https://docs.djangoproject.com/en/6.1/ref/settings/#databases
# Por defecto usa SQLite para desarrollo local. En producción (o para
# apuntar a Neon en cualquier entorno), definir DATABASE_URL en el .env.
#
# Ojo: usamos `env()` (python-decouple) para leer la variable, no
# `dj_database_url.config()` — ese lee directo de os.environ y no ve lo
# que está en el .env vía decouple, así que un DATABASE_URL puesto solo en
# el .env quedaría silenciosamente ignorado.

DATABASE_URL = env('DATABASE_URL', default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}")
DATABASES = {
    'default': dj_database_url.parse(DATABASE_URL, conn_max_age=600),
}

# Neon (y la mayoría de Postgres administrados) exige TLS. Las connection
# strings que da Neon ya traen `sslmode=require`, pero si alguien pega una
# URL sin eso lo forzamos acá — a mano, y solo para Postgres, en vez de
# `ssl_require=True` de dj_database_url (que agrega OPTIONS también contra
# SQLite y rompe ahí).
if 'postgresql' in DATABASES['default']['ENGINE']:
    DATABASES['default'].setdefault('OPTIONS', {})
    DATABASES['default']['OPTIONS'].setdefault('sslmode', 'require')


# Password validation
# https://docs.djangoproject.com/en/6.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# Internationalization
# https://docs.djangoproject.com/en/6.1/topics/i18n/

LANGUAGE_CODE = 'es-ar'

TIME_ZONE = 'America/Argentina/Buenos_Aires'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.1/howto/static-files/

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    # Whitenoise: sirve los estáticos del admin comprimidos y con hash en el
    # nombre, directo desde el proceso de Django — no hace falta nginx ni un
    # servicio de static files aparte en Render.
    'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage'},
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ---------------------------------------------------------------------------
# Producción (Render u otro host detrás de HTTPS). Todo apagado por default
# (DEBUG=True) para que local siga andando igual que siempre; se activa solo
# cuando el entorno pone DEBUG=False.
# ---------------------------------------------------------------------------
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')  # Render/Cloudflare terminan el TLS antes del proceso de Django
    SECURE_HSTS_SECONDS = 60 * 60 * 24 * 7  # 1 semana para arrancar; subir con el tiempo si todo anda bien
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True

# Dominios desde los que el admin acepta POST (login, altas/bajas) por HTTPS.
# Django lo exige aparte de ALLOWED_HOSTS desde la versión que chequea el
# header Origin en vez de Referer. Ej.: https://api.pulsoaustral.com.ar
CSRF_TRUSTED_ORIGINS = env('CSRF_TRUSTED_ORIGINS', default='', cast=Csv())


# ---------------------------------------------------------------------------
# Django REST Framework — API de solo lectura para el frontend. La escritura
# (carga de series, noticias, eventos) se hace desde el admin o desde
# comandos de management, nunca desde un endpoint público.
# ---------------------------------------------------------------------------
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    'PAGE_SIZE': 200,
}

# ---------------------------------------------------------------------------
# CORS — el frontend (Next.js) corre en otro origen/puerto.
# ---------------------------------------------------------------------------
CORS_ALLOWED_ORIGINS = env(
    'CORS_ALLOWED_ORIGINS',
    default='http://localhost:3000,http://127.0.0.1:3000',
    cast=Csv(),
)
