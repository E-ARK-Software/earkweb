import logging
from django.contrib.auth.decorators import login_required
from django.template import loader
from django.http import HttpResponse
import time
from earkweb.models import TestModel
from django.http import JsonResponse
from socket import gethostname, gethostbyname
import pika
import os

logger = logging.getLogger(__name__)


def ready(request):
    response = JsonResponse({'ready': 'true'})
    response.set_cookie("access_token", "test",
                        path='/', secure=False, httponly=False, samesite='lax')
    return response


@login_required
def testmq(request):
    template = loader.get_template('health/testmq.html')
    context = {}
    return HttpResponse(template.render(context=context, request=request))


@login_required
def testmq_publish(request):
    template = loader.get_template('health/testmq_publish.html')
    context = {
    }
    return HttpResponse(template.render(context=context, request=request))


@login_required
def testmq_consume(request):
    template = loader.get_template('health/testmq_consume.html')
    context = {
    }
    return HttpResponse(template.render(context=context, request=request))


@login_required
def publish_message_action(request):
    message = None
    if request.method == 'POST':
        message = request.POST['message']
        url = 'amqp://guest:guest@localhost/%2f'
        params = pika.URLParameters(url)
        params.socket_timeout = 5

        connection = pika.BlockingConnection(params) # Connect to RabbitMQ
        channel = connection.channel() # start a channel
        channel.queue_declare(queue='myexamplequeue') # Declare a queue
        # send a message

        channel.basic_publish(exchange='', routing_key='myexamplequeue', body=message)
        print(" [x] Message sent to consumer")
        connection.close()
    template = loader.get_template('health/testmq_publish.html')
    context = {
        'message': message
    }
    return HttpResponse(template.render(context=context, request=request))


@login_required
def consume_message_action(request):
    message = None
    if request.method == 'POST':
        def pdf_process_function(msg):
          print("Started processing msg: %s (now waiting for 5secs)" % msg)
          time.sleep(5) # delays for 5 seconds
          print("PDF processing finished")
          return

        # Parse CLODUAMQP_URL (fallback to localhost)
        url = 'amqp://guest:guest@localhost/%2f'
        params = pika.URLParameters(url)
        params.socket_timeout = 5
        connection = pika.BlockingConnection(params) # Connect to RabbitMQ
        channel = connection.channel() # start a channel

        # create a function which is called on incoming messages
        def callback(ch, method, properties, body):
            pdf_process_function(body)

        #set up subscription on the queue
        channel.basic_consume(callback,
          queue='myexamplequeue',
          no_ack=True)

        # start consuming (blocks)
        channel.start_consuming()
        connection.close()
        message = "message consumed!"
    template = loader.get_template('health/testmq_consume.html')
    context = {
        'message': message
    }
    return HttpResponse(template.render(context=context, request=request))


@login_required
def index(request):
    query_results = TestModel.objects.all()
    template = loader.get_template('health/index.html')
    context = {
        'query_results': query_results,
        'gethostname': gethostname(),
        'gethostbyname': gethostbyname(gethostname())
    }
    return HttpResponse(template.render(context=context, request=request))


@login_required
def addperson(request):
    firstname = ''
    lastname = ''
    if request.method == 'POST':
        firstname = request.POST['firstname']
        lastname = request.POST['lastname']
        p = TestModel(firstname=firstname, lastname=lastname)
        p.save()
    query_results = TestModel.objects.all()
    template = loader.get_template('health/index.html')
    context = {
        'firstname': firstname,
        'lastname': lastname,
        'query_results': query_results,
    }
    return HttpResponse(template.render(context=context, request=request))



@login_required
def testtask(request):
    from taskbackend.tasks import assign_identifier
    if request.method == 'POST':
        assign_identifier.delay("{\"uid\": \"86b080c0-058c-4064-aa04-6805416df690\"}")
    logger.info(request.method)
    query_results = TestModel.objects.all()
    template = loader.get_template('health/testtask.html')
    context = {

    }
    return HttpResponse(template.render(context=context, request=request))