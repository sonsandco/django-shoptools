import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SECRET_KEY = '123'
DEBUG = True

ALLOWED_HOSTS = []

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'shoptools.checkout',
    'shoptools.cart',
    'shoptools.contrib.catalogue',
    'shoptools.contrib.accounts',
    'shoptools.contrib.emails',
    'shoptools.contrib.paypal',
    'shoptools.contrib.regions',
    'shoptools.contrib.shipping',
    'shoptools.contrib.vouchers'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'full.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.jinja2.Jinja2',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'environment': 'full.jinja_env.environment'
        },
    },
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                # 'django.template.context_processors.debug',
                # 'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                # 'django.template.context_processors.static',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'full.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'full.sqlite3'),
    }
}

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = SERVER_EMAIL = 'noreply@example.com'
CHECKOUT_MANAGERS = [SERVER_EMAIL]

STATIC_URL = '/static/'

COUNTRIES_FIRST = ('NZ', 'AU')
COUNTRIES_FIRST_SORT = ('NZ', 'AU')
COUNTRIES_FIRST_BREAK = '--------'

SHOPTOOLS_ACCOUNTS_MODULE = 'shoptools.contrib.accounts'
SHOPTOOLS_EMAIL_MODULE = 'shoptools.contrib.emails'
SHOPTOOLS_PAYMENT_MODULE = 'shoptools.contrib.paypal'
SHOPTOOLS_REGIONS_MODULE = 'shoptools.contrib.regions'
SHOPTOOLS_SHIPPING_MODULE = 'shoptools.contrib.shipping'
SHOPTOOLS_VOUCHERS_MODULE = 'shoptools.contrib.vouchers'

try:
    from .local import *  # NOQA
except ImportError:
    pass
