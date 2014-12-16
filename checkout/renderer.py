import importlib

from django.conf import settings


TEMPLATE_RENDERER = getattr(settings, 'TEMPLATE_RENDERER', 
                            'coffin.shortcuts.render_to_response')

def renderer_factory():
    '''Gets function used to render templates - by default, 
       coffin.shortcuts.render_to_response, but could be django's, or
       custom.'''

    bits = TEMPLATE_RENDERER.split('.')
    renderer_module = importlib.import_module('.'.join(bits[:-1]))
    return getattr(renderer_module, bits[-1])