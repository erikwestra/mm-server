# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting field 'Profile.email_visible'
        db.delete_column(u'shared_profile', 'email_visible')

        # Deleting field 'Profile.phone_visible'
        db.delete_column(u'shared_profile', 'phone_visible')


    def backwards(self, orm):
        # Adding field 'Profile.email_visible'
        db.add_column(u'shared_profile', 'email_visible',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)

        # Adding field 'Profile.phone_visible'
        db.add_column(u'shared_profile', 'phone_visible',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)


    models = {
        u'shared.conversation': {
            'Meta': {'unique_together': "(('global_id_1', 'global_id_2'),)", 'object_name': 'Conversation'},
            'encryption_key': ('django.db.models.fields.TextField', [], {}),
            'global_id_1': ('django.db.models.fields.TextField', [], {'db_index': 'True'}),
            'global_id_2': ('django.db.models.fields.TextField', [], {'db_index': 'True'}),
            'hidden_1': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'hidden_2': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_message_1': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'last_message_2': ('django.db.models.fields.TextField', [], {'null': 'True'}),
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
            'recipient_text': ('django.db.models.fields.TextField', [], {}),
            'sender_account_id': ('django.db.models.fields.TextField', [], {}),
            'sender_global_id': ('django.db.models.fields.TextField', [], {}),
            'sender_text': ('django.db.models.fields.TextField', [], {}),
            'status': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
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
            'address_1': ('django.db.models.fields.TextField', [], {'default': "''"}),
            'address_1_visible': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'address_2': ('django.db.models.fields.TextField', [], {'default': "''"}),
            'address_2_visible': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'bio': ('django.db.models.fields.TextField', [], {'default': "''"}),
            'bio_visible': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'city': ('django.db.models.fields.TextField', [], {'default': "''"}),
            'city_visible': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'country': ('django.db.models.fields.TextField', [], {'default': "''"}),
            'country_visible': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'date_of_birth': ('django.db.models.fields.DateField', [], {'null': 'True'}),
            'deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'email': ('django.db.models.fields.TextField', [], {'default': "''"}),
            'global_id': ('django.db.models.fields.TextField', [], {'unique': 'True', 'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.TextField', [], {'default': "''"}),
            'name_visible': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'phone': ('django.db.models.fields.TextField', [], {'default': "''"}),
            'picture_id': ('django.db.models.fields.TextField', [], {'default': "''"}),
            'picture_id_visible': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'social_security_number_last_4_digits': ('django.db.models.fields.TextField', [], {'default': "''"}),
            'state_province_or_region': ('django.db.models.fields.TextField', [], {'default': "''"}),
            'state_province_or_region_visible': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'update_id': ('django.db.models.fields.IntegerField', [], {'unique': 'True', 'null': 'True', 'db_index': 'True'}),
            'zip_or_postal_code': ('django.db.models.fields.TextField', [], {'default': "''"}),
            'zip_or_postal_code_visible': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        }
    }

    complete_apps = ['shared']