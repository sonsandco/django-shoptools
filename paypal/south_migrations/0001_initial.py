# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Transaction'
        db.create_table(u'paypal_transaction', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('content_type', self.gf('django.db.models.fields.related.ForeignKey')(related_name='paypal_transactions', to=orm['contenttypes.ContentType'])),
            ('object_id', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('transaction_type', self.gf('django.db.models.fields.CharField')(default='Purchase', max_length=16)),
            ('status', self.gf('django.db.models.fields.CharField')(default='pending', max_length=16)),
            ('amount', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=10, decimal_places=2)),
            ('secret', self.gf('django.db.models.fields.CharField')(default='9427df5f0f9c46af915aad984e3a025e', unique=True, max_length=32, db_index=True)),
            ('result', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal(u'paypal', ['Transaction'])


    def backwards(self, orm):
        # Deleting model 'Transaction'
        db.delete_table(u'paypal_transaction')


    models = {
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'paypal.transaction': {
            'Meta': {'ordering': "('-created', '-id')", 'object_name': 'Transaction'},
            'amount': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '10', 'decimal_places': '2'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'paypal_transactions'", 'to': u"orm['contenttypes.ContentType']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'result': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'secret': ('django.db.models.fields.CharField', [], {'default': "'6f7996c13b6547d6a0335fa4a6d103bb'", 'unique': 'True', 'max_length': '32', 'db_index': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'pending'", 'max_length': '16'}),
            'transaction_type': ('django.db.models.fields.CharField', [], {'default': "'Purchase'", 'max_length': '16'})
        }
    }

    complete_apps = ['paypal']