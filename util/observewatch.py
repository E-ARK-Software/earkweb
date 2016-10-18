import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "earkweb.settings")
import django
django.setup()
from config.configuration import config_path_reception
from earkcore.filesystem.filesystemchangehandler import FileSystemChangeHandler
import time
from watchdog.observers import Observer

observer = Observer()
observer.schedule(FileSystemChangeHandler(), path=config_path_reception)
observer.start()
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    observer.stop()
observer.join()

print "Started directory observation: %s" % config_path_reception