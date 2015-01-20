""" mmServer.settings

    This module defines the various settings for the MMServer project.
"""
import os
import os.path
import sys

import dj_database_url

from mmServer.shared.lib.settingsImporter import SettingsImporter

#############################################################################

# Calculate the absolute path to the top-level directory for our server.

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

#############################################################################

# Load our various custom settings.

import_setting = SettingsImporter(globals(),
                                  custom_settings="mmServer.custom_settings",
                                  env_prefix="MMS_")

import_setting("DEBUG",                                  True)
import_setting("TIME_ZONE",                              "UTC")
import_setting("SET_ALLOWED_HOSTS",                      True)
import_setting("SERVE_STATIC_MEDIA",                     False)
# NOTE: SERVE_STATIC_MEDIA only works if DEBUG is set to True.
import_setting("DATABASE_URL",                           None)
# NOTE: DATABASE_URL uses the following general format:
#           postgres://username:password@host:port/database_name
#       or for a database on the local machine:
#           postgres://username:password@localhost/database_name
import_setting("LOG_DIR",                                os.path.join(ROOT_DIR,
                                                                      "logs"))
import_setting("ENABLE_DEBUG_LOGGING",                   False)
import_setting("DEBUG_LOGGING_DESTINATION",              "file")
# NOTE: KEEP_NONCE_VALUES_FOR is measured in days.  If this has the value
# "none", the None values are kept forever.
import_setting("KEEP_NONCE_VALUES_FOR",                  None)
import_setting("RIPPLED_SERVER_URL",                     None)

#############################################################################

# Our various project settings:

if SET_ALLOWED_HOSTS:
    ALLOWED_HOSTS = [".message.me", ".message.us"]
else:
    ALLOWED_HOSTS = ["*"]

# Django settings for the MMServer project:

TEMPLATE_DEBUG = DEBUG
LANGUAGE_CODE  = 'en-us'
USE_I18N       = True
USE_L10N       = True
USE_TZ         = True
SECRET_KEY     = 't)iyy6l)9i&q@ml54uvozuyy&zdarmv6^&ppc63pui@ft=@2wi'
STATIC_URL     = '/static/'

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',

    # Enable CORS support.

    "mmServer.middleware.cors.CORSMiddleware",
)

ROOT_URLCONF = 'mmServer.urls'

WSGI_APPLICATION = 'mmServer.wsgi.application'

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Install the "south" database migration toolkit.

    'south',

    # Install the various MMServer apps.

    'mmServer.shared',
    'mmServer.api',
)

# Create our "log" directory if we've been configured to write log messages to
# a file.

if (ENABLE_DEBUG_LOGGING and DEBUG_LOGGING_DESTINATION == "file"):
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)

# Start with our default logging configuration.

LOGGING = {
    'version'                  : 1,
    'disable_existing_loggers' : True,
    'handlers'                 : {},
    'loggers'                  : {},
    'formatters'               : {}
}

# Add our custom formatters.

LOGGING['formatters']['plain'] = \
    {'format' : "%(message)s"}

LOGGING['formatters']['timestamped'] = \
    {'format'  : "%(asctime)s %(message)s",
     'datefmt' : "%Y-%m-%d %H:%M:%S"}

# Configure debug logging if it is enabled.

if ENABLE_DEBUG_LOGGING:
    if DEBUG_LOGGING_DESTINATION == "file":
        LOGGING['handlers']['debugger_log'] = \
            {'level'     : "DEBUG",
             'class'     : "logging.FileHandler",
             'filename'  : os.path.join(LOG_DIR, "debug.log"),
             'filters'   : [],
             'formatter' : "timestamped"}
    elif DEBUG_LOGGING_DESTINATION == "console":
        LOGGING['handlers']['debugger_log'] = \
            {'level'     : "DEBUG",
             'class'     : "logging.StreamHandler",
             'filters'   : [],
             'formatter' : "plain"}

    LOGGING['loggers']['mmServer'] = \
        {'handlers'  : ['debugger_log'],
         'level'     : "DEBUG",
         'propogate' : True}

# Set up our database.

if 'test' in sys.argv:
    # Use SQLite for unit tests.
    DATABASES = {'default' : {'ENGINE' : "django.db.backends.sqlite3"}}
else:
    # Use dj_database_url to extract the database settings from the
    # DATABASE_URL setting.
    DATABASES = {'default': dj_database_url.config(default=DATABASE_URL)}

# Configure the CORS middleware.

CORS_ALLOWED_METHODS = "POST, GET, PUT, DELETE, OPTIONS"
CORS_ALLOWED_HEADERS = "Content-Type, Authorization, Content-MD5, Nonce"

