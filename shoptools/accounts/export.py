# -*- coding: utf-8 -*-
import csv


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
    ('First name', lambda o: o.user.first_name),
    ('Last name', lambda o: o.user.last_name),
    ('Address', 'address'),
    ('City', 'city'),
    ('State', 'state'),
    ('Postcode', 'postcode'),
    ('Country', 'country'),
    ('email', lambda o: o.user.email),
    ('Phone', 'phone'),
    ('Is club member', 'club_member'),
)


def generate_csv(qs, file_object):
    csvfile = csv.writer(file_object)

    header = [f[0] for f in ORDER_FIELDS]

    csvfile.writerow(header)

    for obj in qs:
        row = []
        for name, getter in ORDER_FIELDS:
            row.append(getval(obj, getter))

        csvfile.writerow(row)
