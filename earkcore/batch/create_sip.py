import argparse

import logging
logger = logging.getLogger(__name__)


def setup_django():
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../../'))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "earkweb.settings")
    import django
    django.setup()

from workers.tasks import *
from config.configuration import config_path_work


def create_sip(current_task, uuid, packagename):

    logger.info("=================================================================================")
    logger.info("Create SIP %s" % uuid)
    logger.info("=================================================================================")

    logger.info( "Creating SIP for SIP creation process: %s " % uuid )
    work_dir = "%s/%s" % (config_path_work, uuid)

    chain_classes = [ SIPReset, SIPDescriptiveMetadataValidation, SIPPackageMetadataCreation, SIPPackaging, SIPTransferToReception]

    task_context = DefaultTaskContext(uuid, work_dir, 'SIPReset', None, {"packagename": packagename}, None)
    result = None
    for task in chain_classes:
        logger.info("\n------------------------------------------------")
        task_context.task_logger = None
        result = task().apply((task_context,task_context.additional_data), queue='default')

        logger.info( result.status )
        logger.info( result.result.additional_data )
        logger.info( result.result.task_name )
        if current_task is not None:
            current_task.update_state(state='PENDING', meta={'uuid': uuid, 'last_task': result.result.task_name})
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
    # delete working dir after successful processing
    #shutil.rmtree(work_dir)
    # TODO: delete from working directory and remove database entry from earkcore_informationpackage
    logger.info("Finished creating SIP %s" % uuid)
    return task_context

if __name__ == "__main__":
    setup_django()
    parser = argparse.ArgumentParser()
    parser.add_argument('-u','--uuid', help='uuid', required=True)
    args = parser.parse_args()
    create_sip(None, args.uuid)

