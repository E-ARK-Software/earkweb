#!/bin/bash
django-admin makemessages -l de
django-admin makemessages -l es
django-admin makemessages -l en
django-admin compilemessages
