# This is configuration file for SBZ Website.
# This configuration file will load configuration from environment variables.

# Keep these imports here!
import warnings
import os
import json

import environ
from pathlib import Path

from email.utils import getaddresses
from django.core.management.utils import get_random_secret_key

from settings.default import *

# Initialize an env object for `django-environ`
env = environ.Env()

# Set base path of the project, to build paths with.
BASE_DIR = Path(__file__).resolve(strict=True).parent.parent.parent

# Configure database
DATABASES = {
    'default': env.db_url("DATABASE_URL", default=f"sqlite:////{BASE_DIR}/sbz.db")
}


# Override database options if environment variable is given (unsupported by django-environ's env.db() function)
DATABASE_OPTIONS = env.json('DATABASE_OPTIONS', default={})
if DATABASE_OPTIONS:
    DATABASES['default']['OPTIONS'] = DATABASE_OPTIONS

# Make sure these are set correctly in production
ENV                   = env('DJANGO_ENVIRONMENT', default='PRODUCTION')
DEBUG                 = env.bool('DJANGO_DEBUG', default=False)
DEBUG_TOOLBAR         = env.bool('DJANGO_DEBUG', default=False)
TEMPLATE_DEBUG        = env.bool('DJANGO_DEBUG', default=False)
MY_DEBUG_IN_TEMPLATES = False
IGNORE_REQUIRE_SECURE = False
PYDEV_DEBUGGER        = False
PYDEV_DEBUGGER_IP     = None

# Do not redirect to HTTPS, because the nginx proxy container only listens on HTTP
SECURE_SSL_REDIRECT   = False

# Allowed hosts -- localhost and 127.0.0.1 are always allowed, the rest comes from an environment variable.
ALLOWED_HOSTS = [
    "localhost", "127.0.0.1"
] + env.list("DJANGO_ALLOWED_HOSTS", default=[])

# Add Kubernetes POD IP, if running in Kubernetes
KUBE_POD_IP = env("THIS_POD_IP", default="")

ADMINS = getaddresses([env("DJANGO_ADMINS", default="SBZ <www@sbz.utwente.nl>")])
MANAGERS = ADMINS


# Logging settings (log to file and e-mail exceptions to admins)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[%(asctime)s] %(levelname)s %(name)s %(funcName)s (%(filename)s:%(lineno)d) %(message)s',
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        }
    },
    'handlers': {
        'console': {
            'level': 'ERROR',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        },
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler',
            'include_html': False,
        },
    },
    'root': { # all errors go to the console, the general log file and admins
        'level': 'DEBUG',
        'handlers': ['console', 'mail_admins'],
    },
    'loggers': {
        'apps': { # Log all SBZ website errors
            'level': 'DEBUG',
        },
        'django': { # Reset default settings for django
            'handlers': [],
        },
        'django.request': { # Reset default settings for django.request
            'handlers': [],
            'level': 'ERROR',
            'propagate': True,
        },
        'py.warnings': { # Reset default settings for py.warnings
            'handlers': [],
        },
    },
}

# Sentry SDK configuration
DJANGO_SENTRY_DSN = env("DJANGO_SENTRY_DSN", default="")
DJANGO_SENTRY_ENVIRONMENT = env("DJANGO_SENTRY_ENVIRONMENT", default="production")
if DJANGO_SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    sentry_sdk.init(
        dsn=DJANGO_SENTRY_DSN,
        integrations=[
            DjangoIntegration(),
        ],
        # Proportion of requests that are traced for performance monitoring.
        # Keep at (or very very very close to) 0 in production!
        traces_sample_rate=0,
        # Send user details of request to Sentry
        send_default_pii=True,
        auto_session_tracking=False,
        environment=DJANGO_SENTRY_ENVIRONMENT,
    )

# Django authentication backends

###
# Security settings
###

# Only use cookies for HTTPS
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True

# If the proxy tells us the external side is HTTPS, use that
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Make this unique, and don't share it with anybody.
SECRET_KEY = env('DJANGO_SECRET_KEY', default=get_random_secret_key())
UPDATE_FLOW_SECRET = env('UPDATE_FLOW_SECRET', default='')


###
#  E-mail settings
###
EMAIL_BACKEND = env('EMAIL_BACKEND', default='django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST = env('EMAIL_HOST', default='smtp.snt.utwente.nl')
EMAIL_SUBJECT_PREFIX = env('EMAIL_SUBJECT_PREFIX', default='[SBZ]')
EMAIL_PORT = env('EMAIL_PORT', default=25)
EMAIL_TIMEOUT = env('EMAIL_TIMEOUT', default=60.0 * 5)
EMAIL_DELAY = env('EMAIL_DELAY',default=5)
EMAIL_RETURN_PATH = env('EMAIL_RETURN_PATH', default='<bounces@inter-actief.net>')
EMAIL_FROM = env('EMAIL_FROM', default='SBZ <sbz@localhost>')
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default=EMAIL_FROM)
SERVER_EMAIL = env('SERVER_EMAIL', default=EMAIL_FROM)

mv_client_id = env('mv_client_id', default='')
mv_client_secret = env('mv_client_secret', default='')

DE_KLOK_EMAIL = env('DE_KLOK_EMAIL', default='')
DE_KLOK_PASSWORD = env('DE_KLOK_PASSWORD', default='')

FULL_URL_PREFIX = env('FULL_URL_PREFIX', default='https://www.sbz.utwente.nl')
FULL_LIVE_URL_PREFIX = env('FULL_LIVE_URL_PREFIX', default='wss://www.sbz.utwente.nl/ws')
FULL_LIVE_URL_HOST = env('FULL_LIVE_URL_HOST', default='www.sbz.utwente.nl')
FULL_LIVE_URL_PORT = env('FULL_LIVE_URL_PORT', default=80)

HORNET_CLIENT_ID = env('HORNET_CLIENT_ID', default='')
HORNET_CLIENT_SECRET = env('HORNET_CLIENT_SECRET', default='')
