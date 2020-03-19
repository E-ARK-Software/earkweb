#!/bin/bash
cd /opt/python_wsgi_apps/earkweb
git pull
export WORKON_HOME=/opt/PyVirtEnvs/
source /usr/local/bin/virtualenvwrapper.sh 
workon earkweb
pip install -r requirements.txt
python init_solr.py

echo "Restarting earkweb frontend"
kill -9 `ps -aux | grep -v "grep" | grep runserver | awk '{print $2}'`
echo eark | sudo -S service earkweb start

echo "Restarting celery backend"
echo eark | sudo -S service celeryd stop
echo eark | sudo -S service celeryd start

echo "Update finished. You can close the window."
