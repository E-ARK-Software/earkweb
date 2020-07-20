#!/bin/bash
celery -A earkweb.celery control shutdown
celery -A earkweb.celery worker --pool threads -Ofair
