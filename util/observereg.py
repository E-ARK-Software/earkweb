import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "earkweb.settings")
import django
django.setup()

from earkcore.filesystem.consumemessages import consume_regpack

print "Starting new directory registration service"

consume_regpack()

