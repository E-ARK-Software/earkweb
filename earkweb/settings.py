#!/usr/bin/env python
# coding=UTF-8
from __future__ import absolute_import
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))  # noqa: E402
from socket import gethostname, gethostbyname

LOGLEVEL = os.environ.get('LOGLEVEL', 'ERROR')


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter':'standard',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'ERROR'),
        },
        'config': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'DEBUG'),
        },
        'access': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'DEBUG'),
        },
        'earkweb': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'DEBUG'),
        },
        'submission': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'DEBUG'),
        },
        'management': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'DEBUG'),
        },
        'api': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'DEBUG'),
        },
        'resourcesync': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'DEBUG'),
        },
    },
}

import logging.config
logging.config.dictConfig(LOGGING)

from config.configuration import django_secret_key, logfile_celery_proc
from config.configuration import rabbitmq_host
from config.configuration import rabbitmq_port
from config.configuration import rabbitmq_user
from config.configuration import rabbitmq_password
from config.configuration import redis_password
from config.configuration import mysql_host
from config.configuration import mysql_port
from config.configuration import mysql_user
from config.configuration import mysql_password
from config.configuration import mysql_db
from config.configuration import redis_host
from config.configuration import redis_port

LANGUAGE_CODE = 'en'

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGIN_URL = '/earkweb/accounts/login/'
LOGOUT_URL = '/earkweb/accounts/logout/'
LOGIN_REDIRECT_URL = '/earkweb/home/'

LOGIN_EXEMPT_URLS = (
    'earkweb/api/',
    'earkweb/rs/',
    'earkweb/health/',
    'earkweb/health/ready',
)

ADMIN_LOGIN = "test"
ADMIN_PASSWORD = "test"

SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# CAS SSO
# CAS_SERVER_URL = ""

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = django_secret_key
# SECURITY WARNING: turn off in production!
DEBUG = True

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

ALLOWED_HOSTS = [gethostname(), gethostbyname(gethostname()), 'localhost', '127.0.0.1', 'pluto', '10.128.1.3']

STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'static'),
)

SESSION_SAVE_EVERY_REQUEST = True

CELERY_IMPORTS = 'taskbackend.tasks'
#BROKER_URL = "amqp://%s:%s@%s:%d/" % (rabbitmq_user, rabbitmq_password, rabbitmq_host, rabbitmq_port)
#CELERY_RESULT_BACKEND="db+mysql://%s:%s@%s/%s" % (mysql_user, mysql_password, mysql_host, mysql_celerybackend_db)
#CELERY_RESULT_BACKEND = "redis://:%s@%s:%d/0" % (redis_password, redis_host, redis_port)

#BROKER_URL = "redis://:%s@%s:%d/0" % (redis_password, redis_host, redis_port)
BROKER_URL = "amqp://%s:%s@%s:%d/" % (rabbitmq_user, rabbitmq_password, rabbitmq_host, rabbitmq_port)
CELERY_RESULT_BACKEND = "redis://:%s@%s:%d/0" % (redis_password, redis_host, redis_port)

BROKER_CONNECTION_TIMEOUT = 10
BROKER_POOL_LIMIT = 100
CELERY_REDIS_MAX_CONNECTIONS = 20

CELERYBEAT_SCHEDULER = 'djcelery.schedulers.DatabaseScheduler'
CELERY_DEFAULT_QUEUE = 'ingestqueue'
CELERY_TASK_DEFAULT_QUEUE = 'ingestqueue'
CELERY_IGNORE_RESULT = False
TEST_RUNNER = 'djcelery.contrib.test_runner.CeleryTestSuiteRunner'
CELERYD_POOL_RESTARTS = True


# run celery in same process
#CELERY_ALWAYS_EAGER = True

from celery.schedules import crontab
from datetime import timedelta

CELERYBEAT_SCHEDULE = {
    "CheckProcFiles-every-60-seconds": {
        "task": "monitoring.tasks.CheckProcFilesTask",
        "schedule": timedelta(seconds=60),
        "kwargs": {
                'proc_log_path': logfile_celery_proc,
        }
    },
    "CheckStorageMediums-everyday-07:00": {
        "task": "monitoring.tasks.CheckStorageMediumsTask",
        "schedule": crontab(hour=7, minute=0),
        "kwargs": {
                'email': "admin",
        }
    },
}

SWAGGER_SETTINGS = {
    'SECURITY_DEFINITIONS': {
        'api_key': {
            'type': 'apiKey',
            'in': 'header',
            'name': 'Authorization'
        }
    },
}

# Application definition
INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'bootstrapform',
    'earkweb',
    'administration',
    'submission',
    'access',
    'taskbackend',
    'management',
    'health',
    'resourcesync',
    'api',
    'django_tables2',
    'rest_framework',
    'rest_framework.authtoken',
    'rest_framework_swagger',
    'rest_framework_api_key',
    'widget_tweaks',
    'requests',
    'drf_yasg',
)


TEMPLATES[0]['OPTIONS']['context_processors'].append("earkweb.context_processors.environment_variables")
TEMPLATES[0]['OPTIONS']['context_processors'].append('django.template.context_processors.i18n')

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
        'rest_framework_api_key.permissions.HasAPIKey',
    ),
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser',
        'rest_framework.parsers.JSONParser',
    ],
    'DEFAULT_SCHEMA_CLASS':'rest_framework.schemas.coreapi.AutoSchema',
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    )
}

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.locale.LocaleMiddleware',
]

CORS_ORIGIN_ALLOW_ALL = True

# CAS SSO Authentication
#AUTHENTICATION_BACKENDS = (
    #'django_cas_ng.backends.CASBackend',
#)

# OAuth Authentication
#AUTHENTICATION_BACKENDS = (
#    'oauth_backend.auth_backend.AuthenticationBackend',
#)

# Django Authentication
AUTHENTICATION_BACKENDS = (
     'django.contrib.auth.backends.ModelBackend',
)

ROOT_URLCONF = 'earkweb.urls'

WSGI_APPLICATION = 'earkweb.wsgi.application'

# Database
# https://docs.djangoproject.com/en/1.8/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': mysql_db,
        'USER': mysql_user,
        'PASSWORD': mysql_password,
        'HOST': mysql_host,
        'PORT': str(mysql_port),
        'OPTIONS': {
            # "init_command": "SET storage_engine=MyISAM",
            "init_command": "SET default_storage_engine=MyISAM",
        }
    }
}

# Internationalization
# https://docs.djangoproject.com/en/1.8/topics/i18n/
DATETIME_FORMAT = 'Y N jH:i:s.u'
SHORT_DATETIME_FORMAT = 'Y N jH:i:s.u'

TIME_ZONE = 'Europe/Vienna'

USE_I18N = True

USE_L10N = True

USE_TZ = True

LOCALE_PATHS = [
    os.path.join(BASE_DIR, 'locale'),
]
from django.utils.translation import gettext_lazy as _
LANGUAGES = [
    ('en', _('English')),
    ('de', _('German')),
]

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = '/var/www/static/earkweb/'
