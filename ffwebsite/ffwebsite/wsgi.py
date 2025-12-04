"""
WSGI config for ffwebsite project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/
"""

import os
from dotenv import load_dotenv

from django.core.wsgi import get_wsgi_application

from ffwebsite.utils import wait_for_db

# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ffwebsite.settings')
load_dotenv()

wait_for_db()

application = get_wsgi_application()
