from django.dispatch import Signal

checkout_pre_payment = Signal(providing_args=['request'])
checkout_post_payment_pre_success = Signal(
    providing_args=['transaction', 'kwargs']
)
checkout_post_payment_post_success = Signal(
    providing_args=['transaction', 'kwargs']
)
checkout_post_payment_pre_failure = Signal(
    providing_args=['transaction', 'kwargs']
)
checkout_post_payment_post_failure = Signal(
    providing_args=['transaction', 'kwargs']
)
