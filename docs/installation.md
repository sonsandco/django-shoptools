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

3. Add urls to your root urlconf:

    ```python
    urlpatterns = [
        ...
        
        url(r'^checkout/', include('shoptools.checkout.urls')),
        url(r'^catalogue/', include('shoptools.contrib.catalogue.urls')),
        url(r'^cart/', include('shoptools.cart.urls')),
    ]
    ```

4. 
