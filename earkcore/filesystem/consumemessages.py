#!/usr/bin/env python
import pika
from earkcore.models import InformationPackage
from workers.tasks import SIPReset
from workflow.models import WorkflowModules
from earkcore.utils.randomutils import getUniqueID
from workers.tasks import create_ip_folder


def consume_regpack():

    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()

    channel.queue_declare(queue='earkreception')

    def callback(ch, method, properties, body):
        uuid = getUniqueID()
        packagename = body.rsplit('/', 1)[1]
        sip_reset_task = WorkflowModules.objects.get(identifier=SIPReset.__name__)
        InformationPackage.objects.create(path=body, uuid=uuid, statusprocess=0, packagename=packagename, last_task=sip_reset_task)
        job = create_ip_folder.delay(uuid=uuid)
        print("New directory registered: %r (job: %s)" % (body, job.id))

    channel.basic_consume(callback, queue='earkreception', no_ack=True)
    channel.start_consuming()
