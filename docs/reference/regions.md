Regions reference
===

`SHOPTOOLS_REGIONS_MODULE` must provide the following function

Get current region from request:

```
def get_region(user):
    return Region()
```

get current session data from a request

```
def get_data(request):
    return {}
```


Testing
===

To test different regions, use 

http://mysite.com?REMOTE_ADDR=138.68.38.148

where the IP is from the country to test. This will need a fresh browser session as it doesn't update if already set
