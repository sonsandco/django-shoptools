from datetime import datetime
import decimal
import importlib

from django.conf import settings
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey


CART_SESSION_KEY = getattr(settings, 'CART_SESSION_KEY', 'cart')
DEFAULT_CURRENCY = getattr(settings, 'DEFAULT_CURRENCY', 'NZD')
CURRENCY_COOKIE_NAME = getattr(settings, 'CURRENCY_COOKIE_NAME', None)
SHIPPING_CALCULATOR = getattr(settings, 'CART_SHIPPING_CALCULATOR', None)


class OrderLine(models.Model):
    """OrderLine is the db-persisted version of a Cart item. It uses
    the same ICartItem interface (see below) to get details, and is
    intended to be attached to an object you provide. Your object can
    be thought of as an Order, although it doesn't have to be; it
    could equally support a "save this cart for later" feature.

    The advantage of this is that is lets your shop app support
    whatever payment/total cost logic it wants -- it might be a
    straight summing of order lines, it might add shipping, it might
    not involve payment at all.

    This only handles recording items + quantities + calculated prices
    against some object.
    """
    parent_content_type = models.ForeignKey(ContentType,
                                    related_name="orderlines_via_parent")
    parent_object_id = models.PositiveIntegerField()
    parent_object = GenericForeignKey('parent_content_type',
                                      'parent_object_id')

    # item object *must* support ICartItem
    item_content_type = models.ForeignKey(ContentType,
                                          related_name="orderlines_via_item")
    item_object_id = models.PositiveIntegerField()
    item_object = GenericForeignKey('item_content_type', 'item_object_id')

    created = models.DateTimeField(default=datetime.now)
    quantity = models.IntegerField()
    # currency = models.CharField(max_length=3, editable=False, default=DEFAULT_CURRENCY)
    # this supports line totals up to 999,999.99, which is
    # obviously completely excessive.
    total = models.DecimalField(max_digits=8, decimal_places=2)
    description = models.CharField(max_length=255, blank=True)
    options = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        assert isinstance(self.item_object, ICartItem)
        
        if not self.total:
            # if the parent has a currency field, use it
            currency = getattr(self.parent_object, 'currency', DEFAULT_CURRENCY)
            self.total = self.item_object.cart_line_total(self.quantity, currency)

        if not self.description:
            self.description = self.item_object.cart_description()

        return super(OrderLine, self).save(*args, **kwargs)

    def __unicode__(self):
        return u"%s x %s: $%.2f" % (self.description, self.quantity,
                                    self.total)


class CartRow(dict):
    '''Thin wrapper around dict providing some convenience methods for 
       accessing computed information about the row.'''
       
    def __init__(self, **kwargs):
        assert sorted(kwargs.keys()) == ['key', 'line_total', 'options', 'qty']
        return super(CartRow, self).__init__(**kwargs)
    
    def __setitem__(self, *args):
        raise Exception(u"Sorry, CartRow instances are immutable.")
    
    def item(self):
        return Cart.get_item(self['key'])
    
    def line_total(self):
        return self['line_total']
        # return self.item().cart_line_total(self['qty'], currency)


class Cart(object):
    def __init__(self, request):
        self.request = request
        self.currency = request.COOKIES.get(CURRENCY_COOKIE_NAME, DEFAULT_CURRENCY)
        self._data = self.request.session.get(CART_SESSION_KEY, None)

    def _init_session_cart(self):
        if self._data is None:
            data = {"rows": []}
            self._data = self.request.session[CART_SESSION_KEY] = data
    
    def as_dict(self):
        data = {
            'count': self.count(),
            'total': str(self.total()),
            'lines': [],
        }
        for row in self.rows():
            line = dict(row)
            line.update({
                'item': unicode(row.item()),
                'line_total': row.line_total(),
            })
            data['lines'].append(line)
        return data
    
    def empty(self):
        return self._data is None or len(self._data["rows"]) is 0
    
    def add(self, ctype, pk, qty=1, opts={}):
        app_label, model = ctype.split('.')
        ctype_obj = ContentType.objects.get(app_label=app_label, model=model)
        if not issubclass(ctype_obj.model_class(), ICartItem):
            return False
        
        try:
            qty = int(qty)
        except TypeError:
            qty = 1
        
        idx = self.row_index(ctype, pk)
        if idx != None:
            # Already in the cart, so update the existing row
            row = self._data["rows"][idx]
            return self.update_quantity(ctype, pk, qty + row["qty"])
        
        self._init_session_cart()
        row = {'key': Cart.create_key(ctype, pk), 'qty': qty, 'options': opts}
        self._data["rows"].append(row)
        # self.update_total()
        self.request.session.modified = True
        return True
    
    def row_index(self, ctype, pk):
        """Returns the row index for a given ctype/pk, if it's already in the 
           cart, or None otherwise."""
        
        if self._data is not None:
            for i in range(len(self._data["rows"])):
                if self._data["rows"][i]["key"] == self.create_key(ctype, pk):
                    return i
        return None
    
    def remove(self, ctype, pk):
        idx = self.row_index(ctype, pk)
        if idx is not None: # might be 0
            del self._data["rows"][idx]
            # self.update_total()
            self.request.session.modified = True
            return True
        
        return False
    
    def update_options(self, ctype, pk, **options):
        idx = self.row_index(ctype, pk)
        if idx is not None: # might be 0
            self._data["rows"][idx]['options'].update(options)
            self.request.session.modified = True
            return True
                
        return False

    def update_quantity(self, ctype, pk, qty):
        idx = self.row_index(ctype, pk)
        if idx is not None: # might be 0
            self._data["rows"][idx]['qty'] = qty
            # self.update_total()
            self.request.session.modified = True
            return True
                
        return False
    
    @staticmethod
    def get_item(key):
        ctype, pk = Cart.unpack_key(key)
        content_type = ContentType.objects.get_by_natural_key(*ctype.split("."))
        return content_type.get_object_for_this_type(pk=pk)
    
    @staticmethod
    def create_key(ctype, pk):
        return '|'.join((ctype, pk))
    
    @staticmethod
    def unpack_key(key):
        (ctype, pk) = key.split('|')
        return (ctype, pk)
    
    def row(self, **data):
        assert sorted(data.keys()) == ['key', 'options', 'qty']
        item = self.get_item(data['key'])
        data['line_total'] = item.cart_line_total(data['qty'], self.currency)
        return CartRow(**data)
    
    def rows(self):
        if self._data is None:
            return []
        return [self.row(**row) for row in self._data["rows"]]

    def count(self):
        if self._data is None:
            return 0
        return sum(r['qty'] for r in self._data["rows"])
    
    def shipping_cost(self):
        if SHIPPING_CALCULATOR:
            bits = SHIPPING_CALCULATOR.split('.')
            calc_module = importlib.import_module('.'.join(bits[:-1]))
            return getattr(calc_module, bits[-1])(self.rows())
        return 0
    
    def total(self, force=True):
        if self._data is None:
            return 0
        
        subtotal = decimal.Decimal(sum(row.line_total() for row in self.rows()))
        return subtotal + self.shipping_cost()

    def save_to(self, obj):
        assert self._data and (self._data.get("rows", None) is not None)
        for row in self.rows():
            line = OrderLine()
            line.parent_object = obj
            line.item_object = row.item()
            line.quantity = row["qty"]
            line.currency = self.currency
            line.options = unicode(row["options"])
            line.save()
    
    def clear(self):
        if self._data is not None:
            del self.request.session[CART_SESSION_KEY]
            self._data = None


class ICartItem(object):
    def cart_description(self):
        raise NotImplementedError()

    def cart_reference(self):
        raise NotImplementedError()

    def cart_line_total(self, qty, currency):
        # currently must return a float/int, not decimal, due to django's 
        # serialization limitations - see 
        # https://docs.djangoproject.com/en/1.6/topics/http/sessions/#session-serialization
        raise NotImplementedError()
