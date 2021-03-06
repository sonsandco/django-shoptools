# -*- coding: utf-8 -*-

# import os
import csv
# import datetime

from django.db import models


def getval(obj, getter):
    """Gets a value from an object, using a getter which
       can be a callable, an attribute, or a dot-separated
       list of attributes"""
    if callable(getter):
        val = getter(obj)
    else:
        val = obj
        for attr in getter.split('.'):
            val = getattr(val, attr)
            if callable(val):
                val = val()
    if val is True:
        val = 'yes'
    elif val is False:
        val = ''
    return str(val or '')


ORDER_FIELDS = (
    ('Created', lambda o: o.created.strftime('%d/%m/%Y %H:%M')),
    ('Status', 'get_status_display'),
    ('Invoice Number', 'invoice_number'),
    ('Billing Name', 'billing_address.name'),
    ('Billing Address', 'billing_address.address'),
    ('Billing Postcode', 'billing_address.postcode'),
    ('Billing City', 'billing_address.city'),
    ('Billing State', 'billing_address.state'),
    ('Billing Country', 'billing_address.country'),
    ('Billing Email', 'billing_address.email'),
    ('Delivery Name', 'shipping_address.name'),
    ('Delivery Address', 'shipping_address.address'),
    ('Delivery Postcode', 'shipping_address.postcode'),
    ('Delivery City', 'shipping_address.city'),
    ('Delivery State', 'shipping_address.state'),
    ('Delivery Country', 'shipping_address.country'),
    ('Delivery Email', 'shipping_address.email'),
    ('Subtotal', 'subtotal'),
    ('Shipping Cost', 'shipping_cost'),
    ('Discounts', 'total_discount'),
    ('Total', 'total'),
)
LINE_FIELDS = (
    ('Item', 'description'),
    ('Item Quantity', 'quantity'),
    ('Item Total', 'total'),
)


def generate_csv(qs, file_object):
    csvfile = csv.writer(file_object)

    header = [f[0] for f in ORDER_FIELDS]

    # calculate max number of lines
    lines_max = qs.annotate(line_count=models.Count('lines'))\
                  .aggregate(lines_max=models.Max('line_count'))['lines_max']

    for i in range(1, lines_max + 1):
        header += [(f[0] + ' (%s)' % i) for f in LINE_FIELDS]

    csvfile.writerow(header)

    for obj in qs:
        row = []
        for name, getter in ORDER_FIELDS:
            row.append(getval(obj, getter))

        for line in obj.lines.all():
            for name, getter in LINE_FIELDS:
                row.append(getval(line, getter))

        csvfile.writerow(row)
