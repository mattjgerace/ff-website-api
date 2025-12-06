from pymongo import MongoClient
from .base import *

SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]

DATABASES = {
    "default": dj_database_url.parse(os.environ["DATABASE_URL"])
}

MONGO_CLIENT = MongoClient(os.environ["MONGO_URL"])
MONGO_DB = MONGO_CLIENT[os.environ["MONGO_DB_NAME"]]

DEBUG = False