# Python modules
from pathlib import Path
import os
import logging




# Project modules
from settings.conf import * 

# Build paths inside the project like this: BASE_DIR / 'subdir'.
# Path

BASE_DIR = Path(__file__).resolve().parent.parent
ROOT_URLCONF = 'settings.urls'
WSGI_APPLICATION = 'settings.wsgi.application'
ASGI_APPLICATION = 'settings.asgi.application'
AUTH_USER_MODEL = 'users.CustomUser'

print(BASE_DIR)
# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/6.0/howto/deployment/checklist/





# Application definition

DJANGO_AND_THIRD_PARTY_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt'
]

PROJECT_APPS = [
    'apps.users',
    'apps.blogs'
]


INSTALLED_APPS = DJANGO_AND_THIRD_PARTY_APPS + PROJECT_APPS

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


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






# Password validation
# https://docs.djangoproject.com/en/6.0/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/6.0/topics/i18n/

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.0/howto/static-files/

STATIC_URL = 'static/'



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
