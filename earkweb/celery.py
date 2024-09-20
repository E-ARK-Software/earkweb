from __future__ import absolute_import

import os
from json import JSONEncoder
from celery import Celery
from celery.schedules import crontab


# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'earkweb.settings')

app = Celery('earkweb')

# Using a string here means the worker will not have to
# pickle the object when using Windows.
app.config_from_object('django.conf:settings', namespace='CELERY')
#app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
#app.autodiscover_tasks()


# Automatically discover tasks from installed apps
app.autodiscover_tasks()

# Set the parameter for retrying connections on startup
app.conf.broker_connection_retry_on_startup = True

# automatically checks for a special "to_json()" method and uses it to encode the object if found.
def _default(self, obj):
    return getattr(obj.__class__, "to_json", _default.default)(obj)


_default.default = JSONEncoder().default
JSONEncoder.default = _default


# Define a debug task to test task execution
@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))


# Optional: Set the timezone for Celery
app.conf.timezone = 'UTC'

if __name__ == '__main__':
    app.start()
