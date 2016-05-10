# Headless task execution (without gui)

## Table of Contents

- [Remote task execution](#remote-task-execution)
- [Check registered tasks](#check-registered-tasks)
- [Task registration](#task-registration)

### Remote task execution using Django

It is possible to execute tasks remotely using the Django shell:

    cd /path/to/earkweb/
    python manage.py shell
    Python 2.7.6 (default, Mar 22 2014, 22:59:56) 
    [GCC 4.8.2] on linux2
    Type "help", "copyright", "credits" or "license" for more information.
    (InteractiveConsole)
    >>> 

In the Django shell, it is necessary to import the `DefaultTaskContext` class to be able to define parameters for the desired task execution:
    
    >>> from workers.default_task_context import DefaultTaskContext
    >>> dtc = DefaultTaskContext("fd6ab39e-8355-42ec-a2dc-bc4b1d9c1fd2", "/var/data/earkweb/work/fd6ab39e-8355-42ec-a2dc-bc4b1d9c1fd2", "SomeTaskImplementation", None, {}, None)
    
In this case, the DefaultTaskContext object was configured to apply a task on the object identified by the process id "fd6ab39e-8355-42ec-a2dc-bc4b1d9c1fd2" available in the
working directory "/var/data/earkweb/work/fd6ab39e-8355-42ec-a2dc-bc4b1d9c1fd2". The name of the task is "SomeTaskImplementation", and no log file (default location will be used), 
no additional parameters, and no specific PREMIS file is used.

Then the task module, here `SomeTaskImplementation`, is imported and executed asynchronously:
    
    >>> from workers.tasks import SomeTaskImplementation
    >>> result = SomeTaskImplementation().apply_async((dtc,), queue='default')
    
Using `result.status`, the current status is printed out ('SUCCESS' in case it finished successfully):

    >>> result.status
    'SUCCESS'
    
Note that this 'SUCCESS' message only means that the Celery task was executed successfully, it does not mean that the actual task action was performed successfully. To check the 
result of the task action, it is required to check the actual `task_status` (0 means 'success') and the information or error log messages (empty list [] means that no error 
occurred) respectively:

    >>> result.result.task_status
    0
    >>> result.result.task_logger.log
    ['SomeTaskImplementation task e184fb78-6423-4a7a-997e-8a0d1ed55c67', 'Processing package fd6ab39e-8355-42ec-a2dc-bc4b1d9c1fd2', ...]
    >>> result.result.task_logger.err
    []
    
### Check registered tasks

A list of registered tasks can be retrieved by issuing the following command: 

    (earkweb)shs@pluto:/opt/python_wsgi_apps/earkweb$ celery -A earkweb.celeryapp:app inspect registered
    -> celery@<machine>: OK
        * earkweb.celeryapp.debug_task
        * workers.default_task.DefaultTask
        * workers.tasks.AIPCheckMigrationProgress
        * workers.tasks.AIPIndexing
        * workers.tasks.AIPMigrations
        * workers.tasks.AIPPackageMetsCreation
        * workers.tasks.AIPPackaging
        * workers.tasks.AIPRepresentationMetsCreation
        * workers.tasks.AIPStore
        * workers.tasks.AIPValidation
        * workers.tasks.AIPtoDIPReset
        * workers.tasks.CreatePremisAfterMigration
        * workers.tasks.DIPAcquireAIPs
        * workers.tasks.DIPExtractAIPs
        * workers.tasks.DIPImportSIARD
        * workers.tasks.IdentifierAssignment
        * workers.tasks.LilyHDFSUpload
        * workers.tasks.MigrationProcess
        * workers.tasks.SIPClose
        * workers.tasks.SIPDeliveryValidation
        * workers.tasks.SIPDescriptiveMetadataValidation
        * workers.tasks.SIPExtraction
        * workers.tasks.SIPPackageMetadataCreation
        * workers.tasks.SIPPackaging
        * workers.tasks.SIPReset
        * workers.tasks.SIPResetF
        * workers.tasks.SIPRestructuring
        * workers.tasks.SIPValidation
        * workers.tasks.SIPtoAIPReset
        * workers.tasks.extract_and_remove_package


### Task registration

Tasks need to be registered in the database. To do so run the following script:

    python ./workers/scantasks.py
    