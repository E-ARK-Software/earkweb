# Remote task execution using Django (without gui)

Backend Celery tasks can be executed without using the web frontend. 

Before invoking the Django shell, make sure that earkweb's python virtual environment is activated. In the following
command it is assumed that the environment was created in a folder named `venv`:

    source ./venv/bin/activate
    
Then invoke the Django shell in earkweb's code directory:

    cd /path/to/earkweb/
    python manage.py shell
    Python 2.7.6 (default, Mar 22 2014, 22:59:56) 
    [GCC 4.8.2] on linux2
    Type "help", "copyright", "credits" or "license" for more information.
    (InteractiveConsole)
    >>> 
    
In order to execute a tasks it needs to be imported first and then executed using the `delay` function. Depending on 
the task, additional parameters need to be provided in form of a JSON formatted string. Most of the tasks require the 
process ID to identify the working directory. For example, assuming the process ID is 
`a81e9f2c-4ad0-4b8d-8973-d70eacf0fa1d`, the task for validating the content of a working directory can be invoked as 
follows:

    from taskbackend.tasks import validate_working_directory
    result = validate_working_directory.delay('{"process_id": "a81e9f2c-4ad0-4b8d-8973-d70eacf0fa1d"}')

Using `result.status`, the current status is printed out ('SUCCESS' in case it finished successfully):

    result.status
    SUCCESS
    
In case of an error, the task status returns "FAILURE" which in this case would mean, for example, that the task was 
not executed successfully: 

    print result.status
    FAILURE

Each task returns a JSON formatted string which can be passed as input to another task. In this case, the 

    print result.result
    {"process_id": "a81e9f2c-4ad0-4b8d-8973-d70eacf0fa1d"}

A list of registered tasks can be retrieved by issuing the following command: 

    celery inspect registered
