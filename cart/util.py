# -*- coding: utf-8 -*-

from django.template.loader import render_to_string


def get_cart_html(cart, template='cart/cart_snippet.html'):
    return render_to_string(template, {
        'cart': cart
    }, request=cart.request)
