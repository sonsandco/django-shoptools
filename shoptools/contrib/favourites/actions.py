from django.core.exceptions import ObjectDoesNotExist
from django.contrib.contenttypes.models import ContentType

from .models import FavouritesItem


def unpack_instance_key(favourites_list, ctype, pk):
    """
    Retrieves a model instance from a unique key created by
    create_instance_key. If it exists, gets or creates the corresponding
    FavouritesItem, then returns it."""

    content_type = ContentType.objects.get_by_natural_key(*ctype.split('.'))
    try:
        # Check the relevant item still exists
        instance = content_type.get_object_for_this_type(pk=pk)
        instance, _ = FavouritesItem.objects.get_or_create(
            favourites_list=favourites_list, item_content_type=content_type,
            item_object_id=pk)
    except ObjectDoesNotExist:
        instance = None

    return instance


def favourites_action(params=[]):
    """Check for required params and perform action if valid.
       Return in the format

           (success, errors)

       where success is True if the action was performed successfully, False
       if there were errors (i.e. an item is sold out), or None if the request
       is invalid, (i.e. missing a required parameter)

       params is a list of tuples of the form (field, cast_func, required)
    """

    def inner(wrapped_func):
        def action_func(data, favourites_list):
            errors = []
            kwargs = dict(data)

            # TODO review this. Should probably be explicit about what's
            # expected. Would need to change how options are passed in though.
            if 'csrfmiddlewaretoken' in kwargs:
                del kwargs['csrfmiddlewaretoken']

            failure_rv = False
            for field, cast, required in params:
                val = data.get(field)

                if required and not val:
                    failure_rv = None
                    errors.append('%s is required' % field)

                if val:
                    try:
                        kwargs[field] = cast(val)
                    except ValueError:
                        errors.append('%s is invalid' % field)

            if len(errors):
                return (failure_rv, errors)

            return wrapped_func(favourites_list, **kwargs)

        action_func.__name__ = wrapped_func.__name__
        action_func.__doc__ = wrapped_func.__doc__
        return action_func

    return inner


@favourites_action
def delete_favourites_list(favourites_list):
    favourites_list.delete()
    return (True, None)


@favourites_action(params=(
    ('ctype', str, True),
    ('pk', str, True),
))
def toggle(favourites_list, ctype, pk, **opts):
    instance = unpack_instance_key(favourites_list, ctype, pk)

    if favourites_list.get_line(instance, options=opts):
        return favourites_list.remove(instance, options=opts)
    else:
        return favourites_list.add(instance, 1, options=opts)


@favourites_action(params=(
    ('ctype', str, True),
    ('pk', str, True),
    ('quantity', int, True),
))
def quantity(favourites_list, ctype, pk, quantity, **options):
    """Update an item's quantity in the cart. """

    instance = unpack_instance_key(favourites_list, ctype, pk)
    return favourites_list.update_quantity(instance, quantity, options=options)


@favourites_action(params=(
    ('ctype', str, True),
    ('pk', str, True),
    ('quantity', int, False),
))
def add(favourites_list, ctype, pk, quantity=1, **options):
    """Add an item to the cart. """

    instance = unpack_instance_key(favourites_list, ctype, pk)
    return favourites_list.add(instance, quantity, options=options)


@favourites_action()
def clear(favourites_list):
    """Remove everything from the cart. """

    favourites_list.clear()
    return (True, None)
