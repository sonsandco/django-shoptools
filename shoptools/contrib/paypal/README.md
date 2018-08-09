Lightweight wrapper around Paypal's
[Python SDK](https://github.com/paypal/PayPal-Python-SDK)

> pip install paypalrestsdk

Handling billing and shipping addresses correctly within Paypal requires
PayPal Payments Pro, which is only available in US, UK, and Canada.
This module leaves address handling to django-shoptools, and sends a Web
Experience Profile with each payment request telling Paypal not to ask the
user for their address.
