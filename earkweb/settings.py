"""
Django settings for earkweb project.

For more information on this file, see
https://docs.djangoproject.com/en/1.7/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.7/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

TIME_ZONE = 'Europe/Vienna'

LOGIN_URL='/earkweb/accounts/login/'

import celeryapp

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.7/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 's!!9@ii^idp7n+2y=r8%l$y^i#dm-!yx57b+*@aa=$+@3kj=(&'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

TEMPLATE_DEBUG = True

TEMPLATE_DIRS = [os.path.join(BASE_DIR, 'templates')]

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.contrib.auth.context_processors.auth",
    "earkweb.context_processors.django_ip",
    'django.core.context_processors.request',
 )

ALLOWED_HOSTS = []

STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'static'),
)

from config.configuration import mysql_server_ip
import djcelery
djcelery.setup_loader()

CELERY_IMPORTS = ['workers']

BROKER_POOL_LIMIT = 1
BROKER_CONNECTION_TIMEOUT = 10

from config.configuration import rabbitmq_ip
from config.configuration import rabbitmq_port
from config.configuration import rabbitmq_user
from config.configuration import rabbitmq_password

from config.configuration import mysql_server_ip
from config.configuration import mysql_port
from config.configuration import mysql_user
from config.configuration import mysql_password
from config.configuration import mysql_earkweb_db
from config.configuration import mysql_celerybackend_db


from config.configuration import redis_ip
from config.configuration import redis_port

BROKER_URL = "amqp://%s:%s@%s:%d/" % (rabbitmq_user, rabbitmq_password, rabbitmq_ip, rabbitmq_port)
#CELERY_RESULT_BACKEND="db+mysql://%s:%s@%s/%s" % (mysql_user, mysql_password, mysql_server_ip, mysql_celerybackend_db)
CELERY_RESULT_BACKEND = "redis://%s:%d/0" % (redis_ip, redis_port)
CELERY_REDIS_MAX_CONNECTIONS = 1
CELERYBEAT_SCHEDULER='djcelery.schedulers.DatabaseScheduler'
CELERY_DEFAULT_QUEUE = 'default'
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
                'proc_log_path':"/var/log/earkweb/log/proc",
        }
    },
    "CheckStorageMediums-everyday-07:00": {
        "task": "monitoring.tasks.CheckStorageMediumsTask",
        "schedule": crontab(hour=7,minute=0),
        "kwargs": {
                'email':"admin",
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
    'earkcore',
    'sipcreator',
    'search',
    'workers',
    'workflow',
    'sip2aip',
    'config',
    'datamining',
    'django_tables2',
    'djcelery',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)


AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
)

ROOT_URLCONF = 'earkweb.urls'

WSGI_APPLICATION = 'earkweb.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.9/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        #'STORAGE_ENGINE': 'MyISAM',           # STORAGE_ENGINE for MySQL database tables, 'MyISAM' or 'INNODB'
        'NAME': mysql_earkweb_db,                    # Or path to database file if using sqlite3.
        'USER': mysql_user,                      # Not used with sqlite3.
        'PASSWORD': mysql_password,               # Not used with sqlite3.
        'HOST': mysql_server_ip,                           # Set to empty string for localhost. Not used with sqlite3.
        'PORT': str(mysql_port),                           # Set to empty string for default. Not used with sqlite3.
        # This options for storage_engine have to be set for "south migrate" to work.
        'OPTIONS': {
           #"init_command": "SET storage_engine=MyISAM",
           "init_command": "SET default_storage_engine=MyISAM",
        }
    }
}

# Internationalization
# https://docs.djangoproject.com/en/1.7/topics/i18n/

#SHORT_DATETIME_FORMAT = '%d.%m.%y'
#DATETIME_FORMAT = '%d.%m.%y'
DATETIME_FORMAT = 'Y N jH:i:s.u'
SHORT_DATETIME_FORMAT = 'Y N jH:i:s.u'
LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Europe/Vienna'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.7/howto/static-files/

STATIC_URL = '/static/earkweb/'
STATIC_ROOT = '/var/www/static/earkweb/'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
    },
    'handlers': {
        'default': {
            'level':'DEBUG',
            'class':'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/earkweb/earkweb.log',
            'maxBytes': 1024*1024*5, # 5 MB
            'backupCount': 5,
            'formatter':'standard',
        },
        'request_handler': {
            'level':'DEBUG',
            'class':'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/earkweb/request.log',
            'maxBytes': 1024*1024*5, # 5 MB
            'backupCount': 5,
            'formatter':'standard',
        },
        'console': {
            'level':'DEBUG',
            'class':'logging.StreamHandler',
            'formatter':'standard',
        },
    },
    'root': {
        'handlers': ['default', 'console'],
        'level': 'DEBUG'
    },
    'loggers': {
        'django': {
            'handlers': ['default', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'config.configuration': {
                'handlers': ['default', 'console'],
                'level': 'DEBUG',
                'propagate': True,
        },
        'workers': {
                'handlers': ['default', 'console'],
                'level': 'DEBUG',
                'propagate': False,
        },
        'django.request': {
            'handlers': ['request_handler', 'console'],
            'level': 'DEBUG',
            'propagate': False
        },
        'earkcore': {
                 'handlers': ['default', 'console'],
                 'level': 'INFO',
         },
    }
}