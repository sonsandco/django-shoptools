# -*- coding: utf-8 -*-

import csv


FIELDS = (
    ('Amount', 'amount'),
    ('Limit', 'limit'),
    ('Code', 'code'),
    ('Created', lambda o: o.created.strftime('%d/%m/%Y %H:%M')),
    ('Order', 'order_line.parent_object'),
    ('Order ID', 'order_line.parent_object.pk'),
    ('Amount Redeemed', 'amount_redeemed'),
    ('Amount Remaining', lambda o: o.amount_remaining()
        if o.amount_remaining() is not None else ''),
)


def generate_csv(qs, file_object):
    csvfile = csv.writer(file_object)
    header = [f[0] for f in FIELDS]
    csvfile.writerow(header)

    for obj in qs:
        row = []
        for name, getter in FIELDS:
            row.append(getval(obj, getter))

        csvfile.writerow(row)


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
            if val is None:
                break
    if val is True:
        val = 'yes'
    elif val is False:
        val = ''
    return (unicode(val or '')).encode('utf-8')
