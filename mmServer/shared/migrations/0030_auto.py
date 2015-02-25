# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting field 'Profile.location_visible'
        db.delete_column(u'shared_profile', 'location_visible')

        # Deleting field 'Profile.location'
        db.delete_column(u'shared_profile', 'location')

        # Adding field 'Profile.email'
        db.add_column(u'shared_profile', 'email',
                      self.gf('django.db.models.fields.TextField')(default=''),
                      keep_default=False)

        # Adding field 'Profile.email_visible'
        db.add_column(u'shared_profile', 'email_visible',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)

        # Adding field 'Profile.phone'
        db.add_column(u'shared_profile', 'phone',
                      self.gf('django.db.models.fields.TextField')(default=''),
                      keep_default=False)

        # Adding field 'Profile.phone_visible'
        db.add_column(u'shared_profile', 'phone_visible',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)

        # Adding field 'Profile.address_1'
        db.add_column(u'shared_profile', 'address_1',
                      self.gf('django.db.models.fields.TextField')(default=''),
                      keep_default=False)

        # Adding field 'Profile.address_1_visible'
        db.add_column(u'shared_profile', 'address_1_visible',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)

        # Adding field 'Profile.address_2'
        db.add_column(u'shared_profile', 'address_2',
                      self.gf('django.db.models.fields.TextField')(default=''),
                      keep_default=False)

        # Adding field 'Profile.address_2_visible'
        db.add_column(u'shared_profile', 'address_2_visible',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)

        # Adding field 'Profile.city'
        db.add_column(u'shared_profile', 'city',
                      self.gf('django.db.models.fields.TextField')(default=''),
                      keep_default=False)

        # Adding field 'Profile.city_visible'
        db.add_column(u'shared_profile', 'city_visible',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)

        # Adding field 'Profile.state_province_or_region'
        db.add_column(u'shared_profile', 'state_province_or_region',
                      self.gf('django.db.models.fields.TextField')(default=''),
                      keep_default=False)

        # Adding field 'Profile.state_province_or_region_visible'
        db.add_column(u'shared_profile', 'state_province_or_region_visible',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)

        # Adding field 'Profile.zip_or_postal_code'
        db.add_column(u'shared_profile', 'zip_or_postal_code',
                      self.gf('django.db.models.fields.TextField')(default=''),
                      keep_default=False)

        # Adding field 'Profile.zip_or_postal_code_visible'
        db.add_column(u'shared_profile', 'zip_or_postal_code_visible',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)


    def backwards(self, orm):
        # Adding field 'Profile.location_visible'
        db.add_column(u'shared_profile', 'location_visible',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)

        # Adding field 'Profile.location'
        db.add_column(u'shared_profile', 'location',
                      self.gf('django.db.models.fields.TextField')(default=''),
                      keep_default=False)

        # Deleting field 'Profile.email'
        db.delete_column(u'shared_profile', 'email')

        # Deleting field 'Profile.email_visible'
        db.delete_column(u'shared_profile', 'email_visible')

        # Deleting field 'Profile.phone'
        db.delete_column(u'shared_profile', 'phone')

        # Deleting field 'Profile.phone_visible'
        db.delete_column(u'shared_profile', 'phone_visible')

        # Deleting field 'Profile.address_1'
        db.delete_column(u'shared_profile', 'address_1')

        # Deleting field 'Profile.address_1_visible'
        db.delete_column(u'shared_profile', 'address_1_visible')

        # Deleting field 'Profile.address_2'
        db.delete_column(u'shared_profile', 'address_2')

        # Deleting field 'Profile.address_2_visible'
        db.delete_column(u'shared_profile', 'address_2_visible')

        # Deleting field 'Profile.city'
        db.delete_column(u'shared_profile', 'city')

        # Deleting field 'Profile.city_visible'
        db.delete_column(u'shared_profile', 'city_visible')

        # Deleting field 'Profile.state_province_or_region'
        db.delete_column(u'shared_profile', 'state_province_or_region')

        # Deleting field 'Profile.state_province_or_region_visible'
        db.delete_column(u'shared_profile', 'state_province_or_region_visible')

        # Deleting field 'Profile.zip_or_postal_code'
        db.delete_column(u'shared_profile', 'zip_or_postal_code')

        # Deleting field 'Profile.zip_or_postal_code_visible'
        db.delete_column(u'shared_profile', 'zip_or_postal_code_visible')


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
            'address_1': ('django.db.models.fields.TextField', [], {}),
            'address_1_visible': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'address_2': ('django.db.models.fields.TextField', [], {}),
            'address_2_visible': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'city': ('django.db.models.fields.TextField', [], {}),
            'city_visible': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'email': ('django.db.models.fields.TextField', [], {}),
            'email_visible': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'global_id': ('django.db.models.fields.TextField', [], {'unique': 'True', 'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.TextField', [], {}),
            'name_visible': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'phone': ('django.db.models.fields.TextField', [], {}),
            'phone_visible': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'picture_id': ('django.db.models.fields.TextField', [], {}),
            'picture_id_visible': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'state_province_or_region': ('django.db.models.fields.TextField', [], {}),
            'state_province_or_region_visible': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'update_id': ('django.db.models.fields.IntegerField', [], {'unique': 'True', 'null': 'True', 'db_index': 'True'}),
            'zip_or_postal_code': ('django.db.models.fields.TextField', [], {}),
            'zip_or_postal_code_visible': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        }
    }

    complete_apps = ['shared']
