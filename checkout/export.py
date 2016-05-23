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
    return (str(val or '')).encode('utf-8')


ORDER_FIELDS = (
    ('Created', lambda o: o.created.strftime('%d/%m/%Y %H:%M')),
    ('Status', 'get_status_display'),
    ('Invoice Number', 'invoice_number'),
    ('Delivery Name', 'name'),
    ('Delivery Address', 'street'),
    ('Delivery Postcode', 'postcode'),
    ('Delivery City', 'city'),
    ('Delivery State', 'state'),
    ('Delivery Country', 'country'),
    ('Delivery Email', 'email'),
    ('Subtotal', 'subtotal'),
    ('Shipping Cost', 'shipping_cost'),
    ('Discounts', 'total_discount'),
    ('Total', 'total'),

    # ('School', lambda o: ', '.join([s.name for s in o.object.get_schools()])),
    # ('Church', lambda o: ', '.join([c.name for c in o.object.get_churches()])),
    # ('Postal Address', get_default('object.postal_address')),
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



"""
Address Code (refers to Click and Send address book entry)
Delivery Company Name
Delivery Name
Delivery Telephone
Delivery Email
Delivery Address   Line 1
Delivery Address   Line 2
Delivery Address   Line 3
Delivery City/ Suburb
Delivery State
Delivery Postcode (Only mandatory for: Australia; China; Spain; Japan; South Korea; Hong Kong; United States; United Kingdom; France; Singapore)
Delivery Country Code
Service Code *
Article Type *
Length *             (measured in centimeters)
Width *             (measured in centimeters)
Height *             (measured in centimeters)
Declared Weight *         (measured in kilograms)
Extra Cover    0 - no           1 - yes   (defaults to 0 if left blank)
Isurance value (AUD)
Detailed description of goods
Category of Items
Export Declaration Number (mandatory if item value $2000 or over)
Category of items Explanation
Name of person lodging article
Senders instructions in case of non delivery (if leaft blank, defaults to 'Treat as Abandoned')
Return to the following address     (if return selected and if undeliverable)
From Name                              -                              (defaults to Click and Send user profile details if AE to AQ are left blank)
From Company Name                      -                                    (defaults to Click and Send user profile details if AE to AQ are left blank)
From Phone                       -                                (defaults to Click and Send user profile details if AE to AQ are left blank)
From Fax                          -                                    (defaults to Click and Send user profile details if AE to AQ are left blank)
From Email                            -                                            (defaults to Click and Send user profile details if AE to AQ are left blank)
From ABN                       -                                    (defaults to Click and Send user profile details if AE to AQ are left blank)
From Address                Line 1                             -                                    (defaults to Click and Send user profile details if AE to AQ are left blank)
From Address              Line 2                              -                                 (defaults to Click and Send user profile details if AE to AQ are left blank)
From Address            Line 3                              -                                 (defaults to Click and Send user profile details if AE to AQ are left blank)
From City/ Suburb                       -                           (defaults to Click and Send user profile details if AE to AQ are left blank)
From State                       -                              (defaults to Click and Send user profile details if AE to AQ are left blank)
From Postcode                       -                            (defaults to Click and Send user profile details if AE to AQ are left blank)
From Country Code                       -                              (defaults to Click and Send user profile details if AE to AQ are left blank)
Your Reference
Delivery instructions (for domestic deliveries)
Additional services
Box or Irregular shaped item
Sender's customs reference
Importer's reference number
Has commercial value
Item code (1)
Item Description (1)
Item HS Tariff number (1)
Item country of origin (1)
Item quantity (1)
Item unit price (1)
Item unit weight (1)
Item code (2)
Item Description (2)
Item HS Tariff number (2)
Item country of origin (2)
Item quantity (2)
Item unit price (2)
Item unit weight (2)
Item code (3)
Item Description (3)
Item HS Tariff number (3)
Item country of origin (3)
Item quantity (3)
Item unit price (3)
Item unit weight (3)
Item code (4)
Item Description (4)
Item HS Tariff number (4)
Item country of origin (4)
Item quantity (4)
Item unit price (4)
Item unit weight (4)
"""
