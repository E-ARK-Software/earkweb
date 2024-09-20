# oai_pmh/apps.py

from django.apps import AppConfig
import os

class OAIPMHConfig(AppConfig):
    name = 'oai_pmh'
    # Use os.path.dirname(__file__) to dynamically set the correct path
    path = os.path.dirname(__file__)
