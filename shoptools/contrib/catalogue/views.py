from django.shortcuts import render

from shoptools.util import get_favourites_module

from .models import Product

favourites_module = get_favourites_module()


def index(request):
    products = Product.objects.all()

    return render(request, 'catalogue/index.html', {
        'products': products,
    })


def detail(request, product_id):
    product = Product.objects.get(id=product_id)
    favourites_form = None

    if favourites_module:
        favourites_form = favourites_module.forms.AddToFavouritesForm(
            item=product,
            favourites_list_choices=request.user.favourites_lists.values_list(
                'id', 'name'))

    return render(request, 'catalogue/detail.html', {
        'product': product,
        'favourites_form': favourites_form
    })
