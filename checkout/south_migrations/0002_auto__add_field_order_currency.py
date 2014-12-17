# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Order.currency'
        db.add_column(u'checkout_order', 'currency',
                      self.gf('django.db.models.fields.CharField')(default='AUD', max_length=3),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'Order.currency'
        db.delete_column(u'checkout_order', 'currency')


    models = {
        u'checkout.order': {
            'Meta': {'object_name': 'Order'},
            'amount_paid': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '8', 'decimal_places': '2'}),
            'city': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'country': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'currency': ('django.db.models.fields.CharField', [], {'default': "'AUD'", 'max_length': '3'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            'first_name': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1023'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_name': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1023'}),
            'postcode': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'secret': ('django.db.models.fields.CharField', [], {'default': "'1a802c6e30f14478822c9994ca572551'", 'unique': 'True', 'max_length': '32', 'db_index': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'new'", 'max_length': '32'}),
            'street': ('django.db.models.fields.CharField', [], {'max_length': '1023'}),
            'suburb': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'})
        }
    }

    complete_apps = ['checkout']