# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'OrderLine'
        db.create_table(u'cart_orderline', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('parent_content_type', self.gf('django.db.models.fields.related.ForeignKey')(related_name='orderlines_via_parent', to=orm['contenttypes.ContentType'])),
            ('parent_object_id', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('item_content_type', self.gf('django.db.models.fields.related.ForeignKey')(related_name='orderlines_via_item', to=orm['contenttypes.ContentType'])),
            ('item_object_id', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('quantity', self.gf('django.db.models.fields.IntegerField')()),
            ('total', self.gf('django.db.models.fields.DecimalField')(max_digits=8, decimal_places=2)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('options', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal(u'cart', ['OrderLine'])


    def backwards(self, orm):
        # Deleting model 'OrderLine'
        db.delete_table(u'cart_orderline')


    models = {
        u'cart.orderline': {
            'Meta': {'object_name': 'OrderLine'},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'item_content_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'orderlines_via_item'", 'to': u"orm['contenttypes.ContentType']"}),
            'item_object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'options': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'parent_content_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'orderlines_via_parent'", 'to': u"orm['contenttypes.ContentType']"}),
            'parent_object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'quantity': ('django.db.models.fields.IntegerField', [], {}),
            'total': ('django.db.models.fields.DecimalField', [], {'max_digits': '8', 'decimal_places': '2'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['cart']