# Headless task execution (without gui)

## Table of Contents

- [Remote task execution](#remote-task-execution)
- [Check registered tasks](#check-registered-tasks)
- [Task registration](#task-registration)

### Remote task execution using Django

    python manage.py shell
    Python 2.7.6 (default, Mar 22 2014, 22:59:56) 
    [GCC 4.8.2] on linux2
    Type "help", "copyright", "credits" or "license" for more information.
    (InteractiveConsole)
    >>> from workers.default_task_context import DefaultTaskContext
    >>>  dtc = DefaultTaskContext("fd6ab39e-8355-42ec-a2dc-bc4b1d9c1fd2", "/var/data/earkweb/work/fd6ab39e-8355-42ec-a2dc-bc4b1d9c1fd2", "SIPReset", None, {}, None)
    >>> from workers.tasks import SomeTaskImplementation
    >>> result = SomeTaskImplementation().apply_async((dtc,), queue='default')
    >>> result.status
    'SUCCESS'
    >>> result.result.task_logger.log
    ['SIPExtraction task e184fb78-6423-4a7a-997e-8a0d1ed55c67', 'Processing package fd6ab39e-8355-42ec-a2dc-bc4b1d9c1fd2', ...]
    >>> result.result.task_logger.err
    []
    >>> result.result.task_status
    0

### Check registered tasks

    celery -A earkweb.celeryapp:app inspect registered
    -> worker1@<machine>: OK
    *  earkweb.celeryapp.debug_task
    *  workers.tasks.SomeCreation
    *  workers.tasks.add

### Task registration

Tasks need to be registered in the database. To do so run the following script:

    python ./workers/scantasks.py
    