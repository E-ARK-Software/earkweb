#!/bin/bash

WSGI_APP_DIR=/opt/python_wsgi_apps/earkweb
STATIC_DIR=/var/www/static/earkweb

#1 path
update_rights () {
        echo "Update rights in directory ${1}"
        sudo chown -R www-data:epp ${1}
        sudo chmod -R g+w ${1}
}

workon earkweb

update_rights ${WSGI_APP_DIR}

cd ${WSGI_APP_DIR}
echo "Pull from github ..."
sudo -u www-data git pull

update_rights ${WSGI_APP_DIR}

echo "Makemigrations ..."
python manage.py makemigrations workflow
python manage.py makemigrations earkcore

echo "Migrate ..."
python manage.py migrate

update_rights ${STATIC_DIR}

echo "Collectstic ..."
python manage.py collectstatic

update_rights ${STATIC_DIR}

echo "Restart apache web server ..."
sudo service apache2 restart

sleep 2

echo "Update workflow modules ..."
python ./workers/scantasks.py

sleep 2

echo "Restart celery services ..."
sudo ./celery/celeryd/celeryd restart
