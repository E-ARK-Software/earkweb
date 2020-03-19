import pika
import logging
from config.configuration import rabbitmq_host, rabbitmq_port, rabbitmq_user, rabbitmq_password


logger = logging.getLogger(__name__)


def publish_message(queue, message):
    url = "amqp://%s:%s@%s:%s" % (rabbitmq_user, rabbitmq_password, rabbitmq_host, rabbitmq_port)
    url += "/%2f"
    params = pika.URLParameters(url)
    params.socket_timeout = 5
    connection = pika.BlockingConnection(params)
    channel = connection.channel()
    channel.queue_declare(queue=queue)
    channel.basic_publish(exchange='', routing_key=queue, body=message)
    print("Update message sent: %s" % message)
    connection.close()


def get_result_consume_one_message(queue):
    url = "amqp://%s:%s@%s:%s" % (rabbitmq_user, rabbitmq_password, rabbitmq_host, rabbitmq_port)
    url += "/%2f"
    params = pika.URLParameters(url)
    params.socket_timeout = 5
    connection = pika.BlockingConnection(params)
    channel = connection.channel()
    channel.queue_declare(queue=queue)
    method_frame, header_frame, body = channel.basic_get(queue = queue)
    if not method_frame:
        connection.close()
        return None
    else:
        channel.basic_ack(delivery_tag=method_frame.delivery_tag)
        connection.close()
        return body


def consume_messages(queue):

    def update_status(body):
        print("Status updated: %s" % body)

    url = "amqp://%s:%s@%s:%s" % (rabbitmq_user, rabbitmq_password, rabbitmq_host, rabbitmq_port)
    url += "/%2f"
    params = pika.URLParameters(url)
    params.socket_timeout = 5
    connection = pika.BlockingConnection(params)
    channel = connection.channel()

    def callback(ch, method, properties, body):
        update_status(body)

    channel.basic_consume(callback,
      queue=queue,
      no_ack=True)

    channel.start_consuming()
    connection.close()
