#!/bin/bash
echo "Starting earkweb ..."
#cd /earkweb && python3 manage.py runserver 0.0.0.0:8000 
#cd /earkweb && uwsgi --http :8000 --wsgi-file earkweb.py
cd /home/shs/earkweb && uwsgi --ini /home/shs/earkweb/earkweb.ini
