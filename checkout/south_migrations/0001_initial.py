# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Order'
        db.create_table(u'checkout_order', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('secret', self.gf('django.db.models.fields.CharField')(default='4462511c6c434fea8ec7072e5abb60f9', unique=True, max_length=32, db_index=True)),
            ('first_name', self.gf('django.db.models.fields.CharField')(default='', max_length=1023)),
            ('last_name', self.gf('django.db.models.fields.CharField')(default='', max_length=1023)),
            ('email', self.gf('django.db.models.fields.EmailField')(max_length=75)),
            ('street', self.gf('django.db.models.fields.CharField')(max_length=1023)),
            ('suburb', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('postcode', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('city', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('country', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('status', self.gf('django.db.models.fields.CharField')(default='new', max_length=32)),
            ('amount_paid', self.gf('django.db.models.fields.DecimalField')(default=0, max_digits=8, decimal_places=2)),
        ))
        db.send_create_signal(u'checkout', ['Order'])


    def backwards(self, orm):
        # Deleting model 'Order'
        db.delete_table(u'checkout_order')


    models = {
        u'checkout.order': {
            'Meta': {'object_name': 'Order'},
            'amount_paid': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '8', 'decimal_places': '2'}),
            'city': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'country': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            'first_name': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1023'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_name': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1023'}),
            'postcode': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'secret': ('django.db.models.fields.CharField', [], {'default': "'82788b958c514d8d83a116cd7519c061'", 'unique': 'True', 'max_length': '32', 'db_index': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'new'", 'max_length': '32'}),
            'street': ('django.db.models.fields.CharField', [], {'max_length': '1023'}),
            'suburb': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'})
        }
    }

    complete_apps = ['checkout']