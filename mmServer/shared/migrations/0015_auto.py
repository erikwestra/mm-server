# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting model 'CachedRippleAccountID'
        db.delete_table(u'shared_cachedrippleaccountid')

        # Adding field 'PendingMessage.sender_account_id'
        db.add_column(u'shared_pendingmessage', 'sender_account_id',
                      self.gf('django.db.models.fields.TextField')(default=''),
                      keep_default=False)

        # Adding field 'PendingMessage.recipient_account_id'
        db.add_column(u'shared_pendingmessage', 'recipient_account_id',
                      self.gf('django.db.models.fields.TextField')(default=''),
                      keep_default=False)

        # Adding field 'FinalMessage.sender_account_id'
        db.add_column(u'shared_finalmessage', 'sender_account_id',
                      self.gf('django.db.models.fields.TextField')(default=''),
                      keep_default=False)

        # Adding field 'FinalMessage.recipient_account_id'
        db.add_column(u'shared_finalmessage', 'recipient_account_id',
                      self.gf('django.db.models.fields.TextField')(default=''),
                      keep_default=False)


    def backwards(self, orm):
        # Adding model 'CachedRippleAccountID'
        db.create_table(u'shared_cachedrippleaccountid', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('global_id', self.gf('django.db.models.fields.TextField')(unique=True, db_index=True)),
            ('ripple_account_id', self.gf('django.db.models.fields.TextField')(unique=True, db_index=True)),
        ))
        db.send_create_signal(u'shared', ['CachedRippleAccountID'])

        # Deleting field 'PendingMessage.sender_account_id'
        db.delete_column(u'shared_pendingmessage', 'sender_account_id')

        # Deleting field 'PendingMessage.recipient_account_id'
        db.delete_column(u'shared_pendingmessage', 'recipient_account_id')

        # Deleting field 'FinalMessage.sender_account_id'
        db.delete_column(u'shared_finalmessage', 'sender_account_id')

        # Deleting field 'FinalMessage.recipient_account_id'
        db.delete_column(u'shared_finalmessage', 'recipient_account_id')


    models = {
        u'shared.conversation': {
            'Meta': {'unique_together': "(('global_id_1', 'global_id_2'),)", 'object_name': 'Conversation'},
            'encryption_key': ('django.db.models.fields.TextField', [], {}),
            'global_id_1': ('django.db.models.fields.TextField', [], {'db_index': 'True'}),
            'global_id_2': ('django.db.models.fields.TextField', [], {'db_index': 'True'}),
            'hidden_1': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'hidden_2': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_message': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'last_timestamp': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'num_unread_1': ('django.db.models.fields.IntegerField', [], {}),
            'num_unread_2': ('django.db.models.fields.IntegerField', [], {})
        },
        u'shared.finalmessage': {
            'Meta': {'object_name': 'FinalMessage'},
            'conversation': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['shared.Conversation']"}),
            'error': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'hash': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'recipient_account_id': ('django.db.models.fields.TextField', [], {}),
            'recipient_global_id': ('django.db.models.fields.TextField', [], {'db_index': 'True'}),
            'sender_account_id': ('django.db.models.fields.TextField', [], {}),
            'sender_global_id': ('django.db.models.fields.TextField', [], {'db_index': 'True'}),
            'text': ('django.db.models.fields.TextField', [], {}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {})
        },
        u'shared.noncevalue': {
            'Meta': {'object_name': 'NonceValue'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'nonce': ('django.db.models.fields.TextField', [], {'unique': 'True', 'db_index': 'True'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {})
        },
        u'shared.pendingmessage': {
            'Meta': {'object_name': 'PendingMessage'},
            'conversation': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['shared.Conversation']"}),
            'hash': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_status_check': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'db_index': 'True'}),
            'recipient_account_id': ('django.db.models.fields.TextField', [], {}),
            'recipient_global_id': ('django.db.models.fields.TextField', [], {}),
            'sender_account_id': ('django.db.models.fields.TextField', [], {}),
            'sender_global_id': ('django.db.models.fields.TextField', [], {}),
            'text': ('django.db.models.fields.TextField', [], {}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {})
        },
        u'shared.picture': {
            'Meta': {'object_name': 'Picture'},
            'account_secret': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'picture_data': ('django.db.models.fields.TextField', [], {}),
            'picture_filename': ('django.db.models.fields.TextField', [], {}),
            'picture_id': ('django.db.models.fields.TextField', [], {'unique': 'True', 'db_index': 'True'})
        },
        u'shared.profile': {
            'Meta': {'object_name': 'Profile'},
            'account_secret': ('django.db.models.fields.TextField', [], {}),
            'global_id': ('django.db.models.fields.TextField', [], {'unique': 'True', 'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'location': ('django.db.models.fields.TextField', [], {}),
            'location_visible': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.TextField', [], {}),
            'name_visible': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'picture_id': ('django.db.models.fields.TextField', [], {}),
            'picture_visible': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        }
    }

    complete_apps = ['shared']