# -*- coding: utf-8 -*-
from shoptools.cart.views import cart_view

from .import actions


all_actions = ('change_option', )
for action in all_actions:
    locals()[action] = cart_view(getattr(actions, action))
