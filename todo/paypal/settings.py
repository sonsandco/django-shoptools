from django.conf import settings

# settings.DPS_TEMPLATE_ENGINE can be either 'django' or
# 'jinja'/'jinja2' (aliases for the same engine)
TEMPLATE_ENGINE = getattr(settings, 'PAYPAL_TEMPLATE_ENGINE', 'django')
