from vulnerable.settings.base import *

DEBUG = False
#ALLOWED_HOSTS = ['*']

ALLOWED_HOSTS = ['134.209.161.226', 'localhost', 'vulnerable.proyectoprogsd.com']
#
DATABASES = {
    "default": {
        "ENGINE": 'django.db.backends.mysql',
        "NAME": "vulnerable",
        "USER": "vulnerable_user",
        "PASSWORD": "vulnerable_123",
        "HOST": "127.0.0.1",
        "PORT": "3306",
        'OPTIONS': {'init_command': "SET sql_mode='STRICT_TRANS_TABLES'"},

    }
}