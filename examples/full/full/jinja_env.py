try:
    from django.urls import reverse
except ImportError:
    from django.core.urlresolvers import reverse
from django.template import defaultfilters
from jinja2 import Environment

from shoptools.cart import get_cart


def url(view, *args, **kwargs):
    """Match the less-verbose style of the django url templatetag."""
    return reverse(view, args=args, kwargs=kwargs)


def widget_type(bound_field):
    """Describe a form field's widget class, i.e. CheckboxInput.

       Used to render certain inputs differently in a generic form template."""
    return bound_field.field.widget.__class__.__name__


def environment(extensions=[], **options):
    env = Environment(extensions=extensions, **options)
    env.globals.update({
        'url': url,
        'get_cart': get_cart,
    })
    env.filters.update({
        'floatformat': defaultfilters.floatformat,
        'date': defaultfilters.date,
        'widget_type': widget_type
    })
    return env
