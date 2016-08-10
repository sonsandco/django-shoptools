from .models import Country, ShippingOption, Region
from .api import save_to_cart
from .settings import COUNTRY_COOKIE_NAME


def shipping_action(required=[]):
    '''If any required params are missing, return False, otherwise perform
       action and return True.'''

    def inner(wrapped_func):
        def action_func(data, cart):
            if not all(data.get(p) for p in required):
                return (None, None)

            return wrapped_func(data, cart)

        action_func.__name__ = wrapped_func.__name__
        action_func.__doc__ = wrapped_func.__doc__
        return action_func

    return inner


@shipping_action(required=['country', ])
def change_country(data, cart):
    code = data['country']
    try:
        country = Country.objects.get(code=code)
    except Country.DoesNotExist:
        return ({}, None)
    else:
        if country:
            new_dict = save_to_cart(cart, country=country.code)
            return (new_dict, (COUNTRY_COOKIE_NAME, country.code))
    return ({}, None)


@shipping_action(required=['region', ])
def change_region(data, cart):
    region_id = data['region']
    try:
        region = Region.objects.get(id=region_id)
        country = region.get_default_country()
    except (Region.DoesNotExist, Country.DoesNotExist):
        return ({}, None)
    else:
        if country:
            new_dict = save_to_cart(cart, country=country.code)
            return (new_dict, (COUNTRY_COOKIE_NAME, country.code))
    return ({}, None)


@shipping_action(required=['option', ])
def change_option(data, cart):
    option_id = data['option']
    try:
        option = ShippingOption.objects.get(id=option_id)
    except ShippingOption.DoesNotExist:
        return ({}, None)
    else:
        if option:
            new_dict = save_to_cart(cart, option=option.id)
            return (new_dict, None)
    return ({}, None)
