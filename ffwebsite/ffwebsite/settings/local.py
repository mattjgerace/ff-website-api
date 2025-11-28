from .base import *

# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.environ["DB_NAME"], 
        'USER': os.environ["DB_USER"], 
        'PASSWORD': os.environ["DB_PASSWORD"],
        'HOST': os.environ["DB_HOST"], 
        'PORT': os.environ["DB_PORT"],
        'DATABASE_URL': os.environ["DATABASE_URL"]
    }
}

DEBUG = True