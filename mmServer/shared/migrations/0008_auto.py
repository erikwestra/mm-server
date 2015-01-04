# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting field 'Conversation.hidden_by_user_2'
        db.delete_column(u'shared_conversation', 'hidden_by_user_2')

        # Deleting field 'Conversation.hidden_by_user_1'
        db.delete_column(u'shared_conversation', 'hidden_by_user_1')

        # Adding field 'Conversation.hidden_1'
        db.add_column(u'shared_conversation', 'hidden_1',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)

        # Adding field 'Conversation.hidden_2'
        db.add_column(u'shared_conversation', 'hidden_2',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)

        # Adding field 'Conversation.last_message'
        db.add_column(u'shared_conversation', 'last_message',
                      self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2015, 1, 1, 0, 0)),
                      keep_default=False)

        # Adding field 'Conversation.num_unread_1'
        db.add_column(u'shared_conversation', 'num_unread_1',
                      self.gf('django.db.models.fields.IntegerField')(default=0),
                      keep_default=False)

        # Adding field 'Conversation.num_unread_2'
        db.add_column(u'shared_conversation', 'num_unread_2',
                      self.gf('django.db.models.fields.IntegerField')(default=0),
                      keep_default=False)


    def backwards(self, orm):
        # Adding field 'Conversation.hidden_by_user_2'
        db.add_column(u'shared_conversation', 'hidden_by_user_2',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)

        # Adding field 'Conversation.hidden_by_user_1'
        db.add_column(u'shared_conversation', 'hidden_by_user_1',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)

        # Deleting field 'Conversation.hidden_1'
        db.delete_column(u'shared_conversation', 'hidden_1')

        # Deleting field 'Conversation.hidden_2'
        db.delete_column(u'shared_conversation', 'hidden_2')

        # Deleting field 'Conversation.last_message'
        db.delete_column(u'shared_conversation', 'last_message')

        # Deleting field 'Conversation.num_unread_1'
        db.delete_column(u'shared_conversation', 'num_unread_1')

        # Deleting field 'Conversation.num_unread_2'
        db.delete_column(u'shared_conversation', 'num_unread_2')


    models = {
        u'shared.conversation': {
            'Meta': {'object_name': 'Conversation'},
            'global_id_1': ('django.db.models.fields.TextField', [], {'db_index': 'True'}),
            'global_id_2': ('django.db.models.fields.TextField', [], {'db_index': 'True'}),
            'hidden_1': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'hidden_2': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_message': ('django.db.models.fields.DateTimeField', [], {}),
            'num_unread_1': ('django.db.models.fields.IntegerField', [], {}),
            'num_unread_2': ('django.db.models.fields.IntegerField', [], {})
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