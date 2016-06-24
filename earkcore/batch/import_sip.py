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
from config.configuration import config_path_work, config_path_storage

default_map = {'IP.AVID.RA.18005.rep0.seg0':'4294e5eb-6d95-4b31-b544-53eb50711a56',
    'IP.AVID.RA.18005.rep1.seg1':'d9bb0f20-aa8d-43b8-95ca-9bfcb23da832',
    'IP.AVID.RA.18005.rep0.seg4':'db293f24-9cde-4491-912e-4025384dfb5d',
    'IP.AVID.RA.18005.godfather':'dbca4ff0-5d13-4a00-b76a-18325e574f7a',
    'IP.AVID.RA.18005.rep1.seg2':'f57370a8-34e7-4c1d-9253-7fcf972ac46c',
    'IP.AVID.RA.18005.rep1.seg3':'a40384ab-d1c0-4294-b17e-3214bada3497',
    'IP.AVID.RA.18005.rep0.seg2':'c8dde2b4-54e8-4cdd-8e74-ae09edda222e',
    'IP.AVID.RA.18005.rep0.seg1':'106849f7-aed1-4d8e-aefb-2916421b1869',
    'IP.AVID.RA.18005.rep0.seg3':'fc6ce832-a273-49db-a88a-65145d710d35',
    'IP.AVID.RA.18005.rep1.seg4':'d0d04238-5961-4259-b983-3a9036faa05e',
    'IP.AVID.RA.18005.rep1.seg0':'3097ade8-5a29-4620-be0a-8834096cb76b',
    'IP.AVID.RA.18005.rep0.seg5':'e69029db-af03-4d22-b256-4fd2bf75ae2c' }

def import_package(current_task, src_zip, identifier_map = default_map):

    logger.info("=================================================================================")
    logger.info("Import package %s" % src_zip)
    logger.info("=================================================================================")

    sip_uuid = uuid.uuid4().__str__()

    #sip_uuid = '3a7630af-a018-4976-b77c-effd22a6d62e'
    #src_zip = "/home/bartham/earkweb/earkresources/SIP-Import-test/test_sip.zip"
    zip_basename = os.path.basename(src_zip)
    packagename = os.path.splitext(zip_basename)[0]
    logger.info( "Creating package %s " % packagename )
    work_dir = "%s/%s" % (config_path_work, sip_uuid)

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
            {'packagename' : packagename, 'package_file': packagename, 'parent_id':'' ,'parent_path':'', 'storage_dest': config_path_storage, 'storage_loc':'', 'identifier_map':identifier_map }, None)
    result = None
    for task in chain_1_classes:
        logger.info("\n------------------------------------------------")
        task_context.task_logger = None
        result = task().apply((task_context,task_context.additional_data), queue='default')

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
        time.sleep(5)

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


