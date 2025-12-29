from .common import *

DEBUG = True

INTERNAL_IPS = ["127.0.0.1"]

SECRET_KEY = 'django-insecure-*gp58dlx8p)t$%$rb##x637*1l_uh!l(y5&-@opw@t+dt1mb#3'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')