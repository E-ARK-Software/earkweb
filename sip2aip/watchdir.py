import time

import logging
from earkcore.models import InformationPackage

def watchdir():
    """
    Watchdir function is started as a background task by passing the function as
    parameter to earkweb.lib.process.thread.backgroundthread.BackgroundThread.
    The background process is intitialised once in earkweb.urls.
    """

    logger = logging.getLogger(__name__)

    from config.params import init_param
    from config.models import Path
    path_reception = init_param(Path, "init_param", "/var/data/earkweb/reception")
    logger.info( "Observing directory changes: %s" % path_reception )
    import pyinotify

    wm = pyinotify.WatchManager()
    mask = pyinotify.IN_DELETE | pyinotify.IN_CREATE | pyinotify.IN_MODIFY  # watched events


    class EventHandler(pyinotify.ProcessEvent):
        def process_IN_CREATE(self, event):
            ip = InformationPackage(path=event.pathname, statusprocess=0)
            ip.save()
            logger.info(  "New package received %s" % event.pathname )

        def process_IN_DELETE(self, event):
            ip = InformationPackage.objects.get(path=event.pathname)
            ip.delete()
            logger.info(  "Package removed: %s" % event.pathname )

        def process_IN_MODIFY(self, event):
            logger.info(  "Package was modified: %s" % event.pathname )

    handler = EventHandler()
    notifier = pyinotify.Notifier(wm, handler)
    wdd = wm.add_watch(path_reception, mask, rec=True)

    notifier.loop()