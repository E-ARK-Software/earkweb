from watchdog.events import PatternMatchingEventHandler
import pika


class FileSystemChangeHandler(PatternMatchingEventHandler):
    patterns = ["*"]

    def process(self, event):
        """
        event.event_type
            'modified' | 'created' | 'moved' | 'deleted'
        event.is_directory
            True | False
        event.src_path
            path/to/observed/file
        """
        if event.is_directory and event.event_type == "created":
            connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
            channel = connection.channel()
            channel.queue_declare(queue='earkreception')
            channel.basic_publish(exchange='', routing_key='earkreception', body="%s" % event.src_path)

            print("Send new directory created message %s (%s)" % (event.src_path, event.event_type))
            connection.close()

    def on_created(self, event):
        self.process(event)
