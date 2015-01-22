# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting model 'PendingMessage'
        db.delete_table(u'shared_pendingmessage')

        # Deleting model 'FinalMessage'
        db.delete_table(u'shared_finalmessage')

        # Adding model 'Message'
        db.create_table(u'shared_message', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('update_id', self.gf('django.db.models.fields.IntegerField')(unique=True, db_index=True)),
            ('conversation', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['shared.Conversation'])),
            ('hash', self.gf('django.db.models.fields.TextField')()),
            ('timestamp', self.gf('django.db.models.fields.DateTimeField')()),
            ('sender_global_id', self.gf('django.db.models.fields.TextField')()),
            ('recipient_global_id', self.gf('django.db.models.fields.TextField')()),
            ('sender_account_id', self.gf('django.db.models.fields.TextField')()),
            ('recipient_account_id', self.gf('django.db.models.fields.TextField')()),
            ('text', self.gf('django.db.models.fields.TextField')()),
            ('status', self.gf('django.db.models.fields.TextField')()),
            ('last_status_check', self.gf('django.db.models.fields.DateTimeField')(null=True, db_index=True)),
        ))
        db.send_create_signal(u'shared', ['Message'])


    def backwards(self, orm):
        # Adding model 'PendingMessage'
        db.create_table(u'shared_pendingmessage', (
            ('last_status_check', self.gf('django.db.models.fields.DateTimeField')(null=True, db_index=True)),
            ('hash', self.gf('django.db.models.fields.TextField')()),
            ('timestamp', self.gf('django.db.models.fields.DateTimeField')()),
            ('recipient_global_id', self.gf('django.db.models.fields.TextField')()),
            ('sender_global_id', self.gf('django.db.models.fields.TextField')()),
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('conversation', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['shared.Conversation'])),
            ('text', self.gf('django.db.models.fields.TextField')()),
            ('sender_account_id', self.gf('django.db.models.fields.TextField')()),
            ('recipient_account_id', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal(u'shared', ['PendingMessage'])

        # Adding model 'FinalMessage'
        db.create_table(u'shared_finalmessage', (
            ('hash', self.gf('django.db.models.fields.TextField')(null=True)),
            ('timestamp', self.gf('django.db.models.fields.DateTimeField')()),
            ('recipient_global_id', self.gf('django.db.models.fields.TextField')(db_index=True)),
            ('sender_global_id', self.gf('django.db.models.fields.TextField')(db_index=True)),
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('conversation', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['shared.Conversation'])),
            ('text', self.gf('django.db.models.fields.TextField')()),
            ('error', self.gf('django.db.models.fields.TextField')(null=True)),
            ('sender_account_id', self.gf('django.db.models.fields.TextField')()),
            ('recipient_account_id', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal(u'shared', ['FinalMessage'])

        # Deleting model 'Message'
        db.delete_table(u'shared_message')


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
        u'shared.message': {
            'Meta': {'object_name': 'Message'},
            'conversation': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['shared.Conversation']"}),
            'hash': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_status_check': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'db_index': 'True'}),
            'recipient_account_id': ('django.db.models.fields.TextField', [], {}),
            'recipient_global_id': ('django.db.models.fields.TextField', [], {}),
            'sender_account_id': ('django.db.models.fields.TextField', [], {}),
            'sender_global_id': ('django.db.models.fields.TextField', [], {}),
            'status': ('django.db.models.fields.TextField', [], {}),
            'text': ('django.db.models.fields.TextField', [], {}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {}),
            'update_id': ('django.db.models.fields.IntegerField', [], {'unique': 'True', 'db_index': 'True'})
        },
        u'shared.noncevalue': {
            'Meta': {'object_name': 'NonceValue'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'nonce': ('django.db.models.fields.TextField', [], {'unique': 'True', 'db_index': 'True'}),
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