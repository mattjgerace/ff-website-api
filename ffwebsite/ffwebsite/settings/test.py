from .base import *

SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]

DATABASES = {
    "default": dj_database_url.parse(os.environ["DATABASE_URL"])
}

DEBUG = False