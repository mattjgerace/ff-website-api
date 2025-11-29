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

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

SECURE_CONTENT_TYPE_NOSNIFF = True

SECURE_HSTS_SECONDS = 60

SESSION_COOKIE_SECURE = True

CSRF_COOKIE_SECURE = True

SECURE_HSTS_INCLUDE_SUBDOMAINS = True

SECURE_HSTS_PRELOAD = True