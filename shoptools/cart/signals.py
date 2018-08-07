from django.dispatch import Signal


all_actions = ('add', 'quantity', 'options', 'clear', 'set_voucher_codes')
for action in all_actions:
    locals()[action] = Signal(providing_args=['success', 'request'])
