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


def prepare_dip(current_task, uuid, selected_aips):

    logger.info("=================================================================================")
    logger.info("Prepare DIP %s" % uuid)
    logger.info("=================================================================================")

    logger.info("XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXx")
    logger.info("selected_aips: %s" % selected_aips)
    logger.info("XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXx")

    logger.info( "Acquiring and extracting AIPs for DIP creation process: %s " % uuid )
    work_dir = "%s/%s" % (config_path_work, uuid)

    chain_classes = [AIPtoDIPReset, DIPAcquireAIPs, DIPExtractAIPs]

    task_context = DefaultTaskContext(uuid, work_dir, 'AIPtoDIPReset', None, {'selected_aips': selected_aips}, None)
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
    logger.info("Finished acquiring and extracting AIPs for DIP creation process %s" % uuid)
    return task_context

if __name__ == "__main__":
    setup_django()
    parser = argparse.ArgumentParser()
    parser.add_argument('-u','--uuid', help='uuid', required=True)
    args = parser.parse_args()
    prepare_dip(None, args.uuid)

