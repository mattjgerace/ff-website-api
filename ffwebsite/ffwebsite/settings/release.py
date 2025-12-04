from pymongo import MongoClient
from .base import *

# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases


# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql_psycopg2',
#         'NAME': os.environ["DB_NAME"], 
#         'USER': os.environ["DB_USER"], 
#         'PASSWORD': os.environ["DB_PASSWORD"],
#         'HOST': os.environ["DB_HOST"], 
#         'PORT': os.environ["DB_PORT"],
#     }
# }

DATABASES = {
    "default": dj_database_url.parse(os.environ["DATABASE_URL"])
}

MONGO_CLIENT = MongoClient(os.environ["MONGO_URL"])
MONGO_DB = MONGO_CLIENT[os.environ["MONGO_DB_NAME"]]

DATABASES["default"]["OPTIONS"] = {
    "connect_timeout": 10
}

ALLOWED_HOSTS = ['ff-website-api.up.railway.app', 'ff-website-api-dev.up.railway.app']
CSRF_TRUSTED_ORIGINS = ['https://ff-website-api.up.railway.app', 'https://ff-website-api-dev.up.railway.app'] 

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

SECURE_CONTENT_TYPE_NOSNIFF = True

SECURE_HSTS_SECONDS = 60

SESSION_COOKIE_SECURE = True

CSRF_COOKIE_SECURE = True

SECURE_HSTS_INCLUDE_SUBDOMAINS = True

SECURE_HSTS_PRELOAD = True