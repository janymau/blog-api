# Python modules
from pathlib import Path
import os
import logging

# Project modules
from settings.conf import * 


# Path
BASE_DIR = Path(__file__).resolve().parent.parent
ROOT_URLCONF = 'settings.urls'
WSGI_APPLICATION = 'settings.wsgi.application'
ASGI_APPLICATION = 'settings.asgi.application'
AUTH_USER_MODEL = 'users.CustomUser'


# APPS
DJANGO_AND_THIRD_PARTY_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt',
    'drf_spectacular',
    'channels',
    'channels_redis'
]

PROJECT_APPS = [
    'apps.users',
    'apps.blogs',
    'apps.stats',
    'apps.notifications'
]



INSTALLED_APPS = DJANGO_AND_THIRD_PARTY_APPS + PROJECT_APPS

# MIDDLEWARE
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'apps.core.middleware.UserLanguageMiddleware',
]

# TEMPLATES
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'apps' / 'service' / 'templates' ,
        ],
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

# EMAIL SETTINGS
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
EMAIL_FILE_PATH = BASE_DIR / 'apps' /'sent_emails'
DEFAULT_FROM_EMAIL = 'webmaster@localhost'

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True
ENGLISH_LANGUAGE_CODE = 'en'
LANGUAGES = [
    ("en", "English"),
    ("ru", "Russian"),
    ("kz", "Kazakh")
]
LOCALE_PATHS = [
    os.path.join(BASE_DIR, 'locale')
]

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# LOGGING
LOGGING = {
    "version" : 1,
    "disable_existing_loggers" : False,

    "formatters":{

        "simple" : {
            "format" : "[{levelname} : {message}]",
            "style" : "{"
        },
        "verbose" :{
           "format" : "[{asctime} {levelname} {name} {message} {module}]",
           "style" : "{"
        }


    },

    "handlers" : {
        "console" : {
            "class" : "logging.StreamHandler",
            "formatter" : "simple",
            "level" : "DEBUG"
        },
    

        "file" : {
            "class": "logging.handlers.RotatingFileHandler",
            "filename" : os.path.join(BASE_DIR, "logs/app.log"),
            "formatter" : "verbose",
            "level" : "WARNING",
            "maxBytes" : 5 * 1024 * 1024,
            "backupCount" : 3
        },

    },

    "loggers" : {
        "django.request" : {
            "handlers" : ["file"],
            "level" : "WARNING",
            "propagate" : False
        },

        "blogs" : {
            "handlers" : ["console", "file"],
            "level" : "DEBUG",
            "propagate" : False
        },

        "users" : {
            "handlers" : ["console", "file"],
            "level" : "DEBUG",
            "propagate" : False
        }
    }
}
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'