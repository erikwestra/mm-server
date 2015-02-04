# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Profile.deleted'
        db.add_column(u'shared_profile', 'deleted',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)

        # Adding field 'Picture.deleted'
        db.add_column(u'shared_picture', 'deleted',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'Profile.deleted'
        db.delete_column(u'shared_profile', 'deleted')

        # Deleting field 'Picture.deleted'
        db.delete_column(u'shared_picture', 'deleted')


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
            'num_unread_2': ('django.db.models.fields.IntegerField', [], {}),
            'update_id': ('django.db.models.fields.IntegerField', [], {'unique': 'True', 'null': 'True', 'db_index': 'True'})
        },
        u'shared.message': {
            'Meta': {'object_name': 'Message'},
            'action': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'action_params': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'action_processed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'amount_in_drops': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'conversation': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['shared.Conversation']"}),
            'error': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'hash': ('django.db.models.fields.TextField', [], {'null': 'True', 'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'recipient_account_id': ('django.db.models.fields.TextField', [], {}),
            'recipient_global_id': ('django.db.models.fields.TextField', [], {}),
            'sender_account_id': ('django.db.models.fields.TextField', [], {}),
            'sender_global_id': ('django.db.models.fields.TextField', [], {}),
            'status': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'text': ('django.db.models.fields.TextField', [], {}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {}),
            'update_id': ('django.db.models.fields.IntegerField', [], {'unique': 'True', 'null': 'True', 'db_index': 'True'})
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
            'deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'picture_data': ('django.db.models.fields.TextField', [], {}),
            'picture_filename': ('django.db.models.fields.TextField', [], {}),
            'picture_id': ('django.db.models.fields.TextField', [], {'unique': 'True', 'db_index': 'True'}),
            'update_id': ('django.db.models.fields.IntegerField', [], {'unique': 'True', 'null': 'True', 'db_index': 'True'})
        },
        u'shared.profile': {
            'Meta': {'object_name': 'Profile'},
            'account_secret': ('django.db.models.fields.TextField', [], {}),
            'deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'global_id': ('django.db.models.fields.TextField', [], {'unique': 'True', 'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'location': ('django.db.models.fields.TextField', [], {}),
            'location_visible': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.TextField', [], {}),
            'name_visible': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'picture_id': ('django.db.models.fields.TextField', [], {}),
            'picture_visible': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'update_id': ('django.db.models.fields.IntegerField', [], {'unique': 'True', 'null': 'True', 'db_index': 'True'})
        }
    }

    complete_apps = ['shared']