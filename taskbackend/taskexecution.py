import json

from taskbackend.tasks import ingest_pipeline

import logging


logger = logging.getLogger(__name__)


def execute_task(task_input):
    # Get the selected information package from the database
    try:
        # Execute task
        job = ingest_pipeline.delay(json.dumps(task_input))
        data = {"success": True, "id": job.id}
    except AttributeError:
        errdetail = """An error occurred, the task was not initiated."""
        data = {"success": False, "errmsg": "Error ", "errdetail": errdetail}

    return data
