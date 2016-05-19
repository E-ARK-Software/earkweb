import sys
import os
import argparse

import logging
logger = logging.getLogger(__name__)

from celery.result import AsyncResult
def setup_django(src_zip):
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "earkweb.settings")
    import django
    django.setup()


from shutil import copyfile
from workers.tasks import *
from celery import chain
from workflow.models import WorkflowModules
from earkcore.models import InformationPackage


def import_package(current_task, src_zip):

    logger.info("=================================================================================")
    logger.info("Import package %s" % src_zip)
    logger.info("=================================================================================")

    sip_uuid = uuid.uuid4().__str__()

    #sip_uuid = '3a7630af-a018-4976-b77c-effd22a6d62e'
    #src_zip = "/home/bartham/earkweb/earkresources/SIP-Import-test/test_sip.zip"
    zip_basename = os.path.basename(src_zip)
    packagename = os.path.splitext(zip_basename)[0]
    logger.info( "Creating package %s " % packagename )
    work_dir = "/var/data/earkweb/work/"+sip_uuid

    if os.path.exists(work_dir):
        shutil.rmtree(work_dir)
    if not os.path.exists(work_dir):
        os.mkdir(work_dir)

    dst_zip = work_dir+"/"+zip_basename
    logger.info( "copying %s to %s" % (zip_basename, work_dir) )
    copyfile(src_zip, dst_zip)

    sipgen = SIPGenerator(work_dir)
    delivery_mets_file = os.path.join(work_dir, packagename + '.xml')
    sipgen.createDeliveryMets(dst_zip, delivery_mets_file)
    logger.info( "Delivery METS3 stored: %s" % delivery_mets_file )

    #return
    chain_1_classes = [ SIPtoAIPReset, SIPDeliveryValidation, IdentifierAssignment, SIPExtraction, SIPRestructuring, SIPValidation, AIPMigrations]
    test_task = AIPCheckMigrationProgress
    chain_2_classes = [ CreatePremisAfterMigration, AIPRepresentationMetsCreation, AIPPackageMetsCreation, AIPValidation, AIPPackaging, AIPStore]#, LilyHDFSUpload]

    task_context = DefaultTaskContext(sip_uuid, work_dir, 'SIPReset', None,
            {'packagename' : packagename, 'package_file': packagename, 'parent_id':'' ,'parent_path':'', 'storage_dest':'/var/data/earkweb/storage', 'storage_loc':'' }, None)
    result = None
    for task in chain_1_classes:
        logger.info("\n------------------------------------------------")
        task_context.task_logger = None
        result = task().apply((task_context,), queue='default')

        logger.info( result.status )
        logger.info( result.result.additional_data )
        logger.info( result.result.task_name )
        current_task.update_state(state='PENDING', meta={'package_file': zip_basename, 'last_task': result.result.task_name})
        if result.result.task_logger.log:
            logger.info("Execution log ---------------------")
            logger.info("\n".join(result.result.task_logger.log))
        if result.result.task_logger.err:
            logger.info("Execution err ---------------------")
            logger.info("\n".join(result.result.task_logger.err))
        if result.result.task_status != 0:
            logger.info("Stopping chain due to %s task error" % task )
            return
        task_context.additional_data = result.result.additional_data

    last_task = ""
    while not ('migration_complete' in result.result.additional_data and result.result.additional_data['migration_complete']==True):
        task_context.task_logger = None
        result = AIPCheckMigrationProgress().apply((task_context,), queue='default')
        if result.result.task_status != 0:
            logger.info( "Stopping chain due to %s task error" % task )
            return
        time.sleep(25)

    for task in chain_2_classes:
        logger.info( "\n------------------------------------------------" )
        task_context.task_logger = None
        result = task().apply((task_context,), queue='default')

        logger.info(result.status)
        logger.info(result.result.additional_data)
        logger.info(result.result.task_name)
        current_task.update_state(state='PENDING', meta={'package_file': zip_basename, 'last_task': result.result.task_name})
        if result.result.task_logger.log:
            logger.info("Execution log ---------------------")
            logger.info("\n".join(result.result.task_logger.log))
        if result.result.task_logger.err:
            logger.info("Execution err ---------------------")
            logger.info("\n".join(result.result.task_logger.err))
        if result.result.task_status != 0:
            logger.info("Stopping chain due to %s task error" % task)
            return
        task_context.additional_data = result.result.additional_data

    # Synchronize working dir with mysql db
    wf = WorkflowModules.objects.get(identifier = result.result.task_name)
    storage_loc = task_context.additional_data['storage_loc']
    identifier = task_context.additional_data['identifier']
    InformationPackage.objects.create(path=work_dir, uuid=sip_uuid, identifier=identifier, storage_loc=storage_loc, statusprocess=0, packagename=packagename, last_task=wf)
    logger.info("finished")
    return task_context

if __name__ == "__main__":
    setup_django()
    parser = argparse.ArgumentParser()
    parser.add_argument('-f','--file', help='Archive to import', required=True)
    args = parser.parse_args()

    import_package(args.file)


