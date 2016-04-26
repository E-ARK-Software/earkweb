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

TIME_ZONE = 'Europe/Stockholm'

LOGIN_URL='/earkweb/accounts/login/'

import celeryapp


# server settings

SERVER_PROTOCOL_PREFIX = "http://"

SERVER_IP = "10.20.77.1"

# repository

SERVER_REPO_PORT = "12060"

SERVER_REPO = SERVER_PROTOCOL_PREFIX + SERVER_IP + ":" + SERVER_REPO_PORT

SERVER_REPO_PATH= "/repository"

SERVER_TABLE_PATH = "/table"

SERVER_RECORD_PATH = "/record"

SERVER_COLLECTION1 = "/eark1"


SERVER_REPO_RECORD_PATH = SERVER_REPO_PATH + SERVER_TABLE_PATH + SERVER_COLLECTION1 + SERVER_RECORD_PATH

SERVER_REPO_RECORD_CONTENT_QUERY = SERVER_REPO + SERVER_REPO_RECORD_PATH + "/{0}/field/n$content/data?ns.n=org.eu.eark"

# solr

SERVER_SOLR_PORT = "8983"

SERVER_SOLR_PATH = "/solr"

SERVER_SOLR = SERVER_PROTOCOL_PREFIX + SERVER_IP + ":" + SERVER_SOLR_PORT

SERVER_SOLR_QUERY_URL = SERVER_SOLR + SERVER_SOLR_PATH + "/eark1/select?q={0}&wt=json" 

# hdfs storage service

SERVER_HDFS = SERVER_PROTOCOL_PREFIX + "localhost" + ":8081/hsink/fileresource"

SERVER_HDFS_AIP_QUERY = SERVER_HDFS + "/retrieve_newest?file={0}"

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.7/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 's!!9@ii^idp7n+2y=r8%l$y^i#dm-!yx57b+*@aa=$+@3kj=(&'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

TEMPLATE_DEBUG = True

TEMPLATE_DIRS = [os.path.join(BASE_DIR, 'templates')]

ALLOWED_HOSTS = []

STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'static'),
)


#CAS_REDIRECT_URL = '/earkweb/search'
#LOGIN_URL = '/earkweb/accounts/login/'
#LOGOUT_URL = '/earkweb/accounts/logout/'

import djcelery
djcelery.setup_loader()

CELERY_IMPORTS = ['workers']

BROKER_URL = 'amqp://guest:guest@localhost:5672/'
CELERY_RESULT_BACKEND='db+mysql://arkiv:arkiv@localhost/celerydb'
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
    'djcelery',
    'earkcore',
    'sipcreator',
    'search',
    'workers',
    'workflow',
    'sip2aip',
    'config',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    
#    'django_cas.middleware.CASMiddleware', 'django.contrib.admindocs.middleware.XViewMiddleware',
)


AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    # 'django_cas.backends.CASBackend',
)

#CAS_SERVER_URL = 'https://earkdev.ait.ac.at:8443/cas/login'

ROOT_URLCONF = 'earkweb.urls'

WSGI_APPLICATION = 'earkweb.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.7/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        #'STORAGE_ENGINE': 'MyISAM',           # STORAGE_ENGINE for MySQL database tables, 'MyISAM' or 'INNODB'
        'NAME': 'eark',                    # Or path to database file if using sqlite3.
        'USER': 'arkiv',                      # Not used with sqlite3.
        'PASSWORD': 'arkiv',               # Not used with sqlite3.
        'HOST': '',                           # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                           # Set to empty string for default. Not used with sqlite3.
        # This options for storage_engine have to be set for "south migrate" to work.
        'OPTIONS': {
           "init_command": "SET storage_engine=MyISAM",
        }
    }
}
#DATABASES = {
#    'default': {
#        'ENGINE': 'django.db.backends.sqlite3',
#        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
#    }
#}



# Internationalization
# https://docs.djangoproject.com/en/1.7/topics/i18n/

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
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': '/var/log/earkweb/earkweb.log',
        },
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'earkcore.models': { 
		'handlers': ['file', 'console'], 
		'level': 'DEBUG', 
		'propagate': True,
	},
    },
    'loggers': {
        'django.request': {
            'handlers': ['file', 'console'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
    'loggers': {
        'sipcreator.views': {
            'handlers': ['file', 'console'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'sipcreator.query': {
            'handlers': ['file', 'console'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
    'loggers': {
        'search.views': {
            'handlers': ['file', 'console'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'search.query': {
            'handlers': ['file', 'console'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
    'loggers': {
        'workflow.views': {
            'handlers': ['file', 'console'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
    'loggers': {
        'sip2aip.views': {
            'handlers': ['file', 'console'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'sip2aip.watchdir': {
            'handlers': ['file', 'console'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}
