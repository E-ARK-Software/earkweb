# Manual installation

## Dependencies

### Debian packages

1. Install jhove (file format characterisation):

        sudo apt-get install summain jhove  
    
2. Install pgmagick (python image conversion:    
    
        sudo apt-get install graphicsmagick
        sudo apt-get install libgraphicsmagick++1-dev libboost-python-dev
    
3. Install pdfhtml for PDF to HTML conversion:

        sudo apt-get install pdftohtml

### Additional python modules

#### fido

[fido](https://github.com/openpreserve/fido)

4. Install fido:

        wget https://github.com/openpreserve/fido/archive/1.3.2-81.tar.gz
        tar -xzvf 1.3.2-81.tar.gz
        cd fido-1.3.2-81
        sudo python setup.py install

5. Update filetype signatures:

        cd fido
        python update_signatures.py

#### ghostscript

6. Install ghostscript (PDF to PDF/A conversion):

    6.1. Download: [Ghostscript 9.18] (http://downloads.ghostscript.com/public/ghostscript-9.18.tar.gz):
    
        wget http://downloads.ghostscript.com/public/old-gs-releases/ghostscript-9.18.tar.gz

    6.2. Installation: [how to install] (http://www.ghostscript.com/doc/9.18/Install.htm):

        tar -xzf ghostscript-9.18.tar.gz
        cd ghostscript-9.18
        ./configure
        make
        make install

## Set up

### Checkout and install dependencies

7. Checkout project

        git clone https://github.com/eark-project/earkweb
        
    Optionally, define the earkweb root directory in the environment variable EARKWEB:

        cd earkweb
        export EARKWEB=`pwd`
    
    If this variable is set, it can be used to execute commands explained further down in this README file.

8. Create virtual environment (python)

    Install virtual environment python packages (requires pip: https://pypi.python.org/pypi/pip):

        sudo pip install virtualenv
        sudo pip install virtualenvwrapper

    Create a virtual environment (e.g. named earkweb) to install additional python packages separately from the default python installation.
    
        mkvirtualenv earkweb
        workon earkweb

    Create a directory for your virtual environments and set the environment variable (e.g. in your ~/.bashrc):
    
        export WORKON_HOME=~/Envs
        source /usr/local/bin/virtualenvwrapper.sh
        
    If the virtual environment is active, this is shown by a prefix in the console:
    
        (earkweb)user@machine:~$
        
    If it is not active, it can be activated as follows:
    
        user@machine:~$ workon earkweb

    And it can be deactivated again by typing:
    
        deactivate

9. Install additional libraries

        pip install -r ${EARKWEB}/requirements.txt
        
   Common errors occurring during python package installation are due to missing linux package dependencies, therefore it might be necessary to install additional packages:
        
        sudo apt-get install libmysqlclient-dev libffi-dev unixodbc-dev python-lxml libgeos-dev
        sudo easy_install --upgrade pytz
        
10. Create directories making sure the user running earkweb has rights to reading and write:

        sudo mkdir -p /var/data/earkweb/{reception,storage,work,ingest,access}
        sudo chown -R <user>:<group> /var/data/earkweb/
        sudo mkdir -p /var/log/earkweb
        sudo chown <user>:<group> /var/log/earkweb

## Celery services

### Start daemon 

11. Make sure the virtual environment "earkweb" is active (prefix "earkweb" in terminal) and change to the earkweb directory:

        (earkweb)<user>@<machine>:~/$ cd ${EARKWEB}    

12. Start the daemon from command line:
    
        python manage.py celeryd -E
    
### Create and initialize database

13. Prepare databases (one main database for the frontend (eark) and one for the celery backend (celerydb):

    Install mysql database if not available on your system:
    
        sudo apt-get install mysql-server
    
    A MySQL database is defined in `${EARKWEB}/settings.py`.
    Create the database first and 
    
    Login to mysql:
    
        mysql -u root -p<rootpassword>
        
    Create user 'arkiv':
    
        CREATE USER 'arkiv'@'localhost' IDENTIFIED BY 'arkiv';
        
    Create database 'eark':
        
        mysql> create database eark;
        
    Grant access to user 'arkiv':

        GRANT ALL ON eark.* TO arkiv@localhost IDENTIFIED BY 'arkiv';
        
    Create another database for Celery:
    
        mysql> create database celerydb;

    And grant rights to use datase celery for user 'arkiv':
    
        mysql> GRANT ALL ON celerydb.* TO arkiv@localhost IDENTIFIED BY 'arkiv';


14. Create database schema based on the model and apply initialise the database:

        python manage.py makemigrations
        python manage.py migrate

    Required software packages for django/celery/mysql support:

        pip install django
        pip install -U celery
        pip install django-celery
        pip install MySQL-python
        
15. Once the database is running, tasks need to be registered in the database. To do so run the following script in the `${EARKWEB}` directory:

        python ./workers/scantasks.py
        
# Run in development mode

### Run web application (development mode)

1. Change to the *earkweb* directory:

        cd <earkweb_install_path>/earkweb
        
1. Start web application

    Start the web application from the command line using the command:

        python manage.py runserver
        
    A message similar to the one below should be shown in case of success
    
        System check identified no issues (0 silenced).
        June 18, 2015 - 08:34:56
        Django version 1.7, using settings 'earkweb.settings'
        Starting development server at http://127.0.0.1:8000/
        Quit the server with CONTROL-C.
        
    Open web browser at http://127.0.0.1:8000/