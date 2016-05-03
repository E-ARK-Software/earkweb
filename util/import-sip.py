import sys
import os
import argparse

from celery.result import AsyncResult

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "earkweb.settings")
import django
django.setup()

#import uuid
from shutil import copyfile
from workers.default_task_context import DefaultTaskContext
from workers.tasks import *
from celery import chain
from workflow.models import WorkflowModules
from earkcore.models import InformationPackage
from django.conf import settings
#from earkcore.utils.randomutils import getUniqueID
def main(src_zip):

    sip_uuid = uuid.uuid4().__str__()

    #sip_uuid = '3a7630af-a018-4976-b77c-effd22a6d62e'
    #src_zip = "/home/bartham/earkweb/earkresources/SIP-Import-test/test_sip.zip"
    zip_basename = os.path.basename(src_zip)
    packagename = os.path.splitext(zip_basename)[0]
    print "Creating package %s " % packagename
    work_dir = "/var/data/earkweb/work/"+sip_uuid

    if os.path.exists(work_dir):
        shutil.rmtree(work_dir)
    if not os.path.exists(work_dir):
        os.mkdir(work_dir)

    dst_zip = work_dir+"/"+zip_basename
    print "copying %s to %s" % (zip_basename, work_dir)
    copyfile(src_zip, dst_zip)

    sipgen = SIPGenerator(work_dir)
    delivery_mets_file = os.path.join(work_dir, packagename + '.xml')
    sipgen.createDeliveryMets(dst_zip, delivery_mets_file)
    print "Delivery METS3 stored: %s" % delivery_mets_file

    #return
    chain_1_classes = [ SIPtoAIPReset, SIPDeliveryValidation, IdentifierAssignment, SIPExtraction, SIPRestructuring, SIPValidation, AIPMigrations]
    test_task = AIPCheckMigrationProgress
    chain_2_classes = [ CreatePremisAfterMigration, AIPRepresentationMetsCreation, AIPPackageMetsCreation, AIPValidation, AIPPackaging, AIPStore]#, LilyHDFSUpload]

    task_context = DefaultTaskContext(sip_uuid, work_dir, 'SIPReset', None,
            {'packagename' : packagename, 'package_file': packagename, 'parent_id':'' ,'parent_path':'', 'storage_dest':'/var/data/earkweb/storage', 'storage_loc':'' }, None)
    result = None
    for task in chain_1_classes:
        print "\n------------------------------------------------"
        task_context.task_logger = None
        result = task().apply((task_context,), queue='default')

        print result.status
        print result.result.additional_data
        print result.result.task_name
        if result.result.task_logger.log:
            print "Execution log ---------------------"
            print "\n".join(result.result.task_logger.log)
        if result.result.task_logger.err:
            print "Execution err ---------------------"
            print "\n".join(result.result.task_logger.err)
        if result.result.task_status != 0:
            print "Stopping chain due to %s task error" % task
            return
        task_context.additional_data = result.result.additional_data

    last_task = ""
    while not ('migration_complete' in result.result.additional_data and result.result.additional_data['migration_complete']==True):
        task_context.task_logger = None
        result = AIPCheckMigrationProgress().apply((task_context,), queue='default')
        if result.result.task_status != 0:
            print "Stopping chain due to %s task error" % task
            return
        time.sleep(5)

    for task in chain_2_classes:
        print "\n------------------------------------------------"
        task_context.task_logger = None
        result = task().apply((task_context,), queue='default')

        print result.status
        print result.result.additional_data
        print result.result.task_name
        if result.result.task_logger.log:
            print "Execution log ---------------------"
            print "\n".join(result.result.task_logger.log)
        if result.result.task_logger.err:
            print "Execution err ---------------------"
            print "\n".join(result.result.task_logger.err)
        if result.result.task_status != 0:
            print "Stopping chain due to %s task error" % task
            return
        task_context.additional_data = result.result.additional_data

    # Synchronize working dir with mysql db
    wf = WorkflowModules.objects.get(identifier = result.result.task_name)
    InformationPackage.objects.create(path=work_dir, uuid=sip_uuid, statusprocess=0, packagename=packagename, last_task=wf)
    print "finished"

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-f','--file', help='Archive to import', required=True)
    args = parser.parse_args()

    main(args.file)


