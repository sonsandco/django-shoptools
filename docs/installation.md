Requirements
---

- Python 3.4+
- Django 1.8+


Basic installation
---

1. Install the shoptools library

    ```
    pip install django-shoptools
    ```

2. Add the following to `INSTALLED_APPS`:

    ```python
    INSTALLED_APPS = [
        ...

        'shoptools.checkout',
        'shoptools.contrib.catalogue',
    ]
    ```

   `shoptools.contrib.catalogue` provides an example shop app, you'll want to create your own for an actual shop.

3. Add urls to your root urlconf:

    ```python
    urlpatterns = [
        ...

        url(r'^checkout/', include('shoptools.checkout.urls')),
        url(r'^catalogue/', include('shoptools.contrib.catalogue.urls')),
        url(r'^cart/', include('shoptools.cart.urls')),
    ]
    ```

4. Create templates for the checkout and catalogue apps - examples in `shoptools/checkout/jinja2/checkout` and `shoptools/contrib/catalogue/jinja2/catalogue` are a good starting point. Copy these into your project's template directory and edit.


Payment
---

TODO

1. Add a valid payment module to settings, e.g.:

    ```python
    SHOPTOOLS_PAYMENT_MODULE = 'dps.transactions'
    ```

2. See the [payments reference](reference/payment.md) for more information

Shipping
---

1. Add the shipping module to settings, e.g.:

    ```python
    SHOPTOOLS_SHIPPING_MODULE = 'shoptools.contrib.shipping'
    ```

2. Add `'shoptools.contrib.shipping'` to `INSTALLED_APPS`

3. Add urls to your root urlconf:

  ```python
  urlpatterns = [
      ...

      url(r'^shipping/', include('shoptools.contrib.shipping.urls')),
  ]
  ```

4. For custom shipping functionality, create your own shipping module. See [shipping reference](reference/shipping.md)


Regions
---

1. Add the region module to settings, e.g.:

    ```python
    SHOPTOOLS_REGIONS_MODULE = 'shoptools.contrib.regions'
    ```

2. Add `'shoptools.contrib.regions'` to `INSTALLED_APPS`

3. Add urls to your root urlconf:

  ```python
  urlpatterns = [
      ...

      url(r'^regions/', include('shoptools.contrib.regions.urls')),
  ]
  ```

User accounts
---

1. Add the accounts module to settings, e.g.:

    ```python
    SHOPTOOLS_ACCOUNTS_MODULE = 'shoptools.contrib.accounts'
    ```

2. Add `'shoptools.contrib.accounts'` to `INSTALLED_APPS`

3. Add `'shoptools.contrib.accounts.auth_backends.EmailBackend'` to `AUTHENTICATION_BACKENDS`

4. Add urls to your root urlconf:

  ```python
  urlpatterns = [
      ...

      url(r'^accounts/', include('shoptools.contrib.accounts.urls')),
  ]

Vouchers
---

1. Add the vouchers module to settings, e.g.:

    ```python
    SHOPTOOLS_VOUCHERS_MODULE = 'shoptools.contrib.vouchers'
    ```

2. Add `'shoptools.contrib.vouchers'` to `INSTALLED_APPS`



Save logged-in user's cart across sessions
---

1. Add `'shoptools.cart'` to `INSTALLED_APPS` and run `./manage.py migrate`
