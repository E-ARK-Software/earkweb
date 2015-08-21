import time
import os
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

    def isPackageFile(path):
        filename, file_ext = os.path.splitext(path)
        return (file_ext == '.tar' or file_ext == '.tar.gz')


    class EventHandler(pyinotify.ProcessEvent):
        ips = InformationPackage.objects.all()
        for ip in ips:
            if isPackageFile(ip.path) and not os.path.isfile(ip.path):
                ip = InformationPackage.objects.get(path=ip.path)
                ip.delete()
                logger.info( "Non existing package removed from reception: %s" % ip.path )

        def process_IN_CREATE(self, event):
            if isPackageFile(event.pathname):
                ip = InformationPackage(path=event.pathname, statusprocess=0)
                ip.save()
                logger.info( "New package received %s" % event.pathname )

        def process_IN_DELETE(self, event):
            if isPackageFile(event.pathname):
                ip = InformationPackage.objects.get(path=event.pathname)
                ip.delete()
                logger.info( "Package removed: %s" % event.pathname )

        def process_IN_MODIFY(self, event):
            #logger.info(  "Package was modified: %s" % event.pathname )
            pass

    handler = EventHandler()
    notifier = pyinotify.Notifier(wm, handler)
    wdd = wm.add_watch(path_reception, mask, rec=True)

    notifier.loop()