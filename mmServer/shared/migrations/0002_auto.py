# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting field 'Profile.image_url'
        db.delete_column(u'shared_profile', 'image_url')

        # Adding field 'Profile.name_visible'
        db.add_column(u'shared_profile', 'name_visible',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)

        # Adding field 'Profile.location_visible'
        db.add_column(u'shared_profile', 'location_visible',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)

        # Adding field 'Profile.picture_url'
        db.add_column(u'shared_profile', 'picture_url',
                      self.gf('django.db.models.fields.TextField')(default=None),
                      keep_default=False)

        # Adding field 'Profile.picture_url_visible'
        db.add_column(u'shared_profile', 'picture_url_visible',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)


    def backwards(self, orm):

        # User chose to not deal with backwards NULL issues for 'Profile.image_url'
        raise RuntimeError("Cannot reverse this migration. 'Profile.image_url' and its values cannot be restored.")
        
        # The following code is provided here to aid in writing a correct migration        # Adding field 'Profile.image_url'
        db.add_column(u'shared_profile', 'image_url',
                      self.gf('django.db.models.fields.TextField')(),
                      keep_default=False)

        # Deleting field 'Profile.name_visible'
        db.delete_column(u'shared_profile', 'name_visible')

        # Deleting field 'Profile.location_visible'
        db.delete_column(u'shared_profile', 'location_visible')

        # Deleting field 'Profile.picture_url'
        db.delete_column(u'shared_profile', 'picture_url')

        # Deleting field 'Profile.picture_url_visible'
        db.delete_column(u'shared_profile', 'picture_url_visible')


    models = {
        u'shared.profile': {
            'Meta': {'object_name': 'Profile'},
            'global_id': ('django.db.models.fields.TextField', [], {'unique': 'True', 'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'location': ('django.db.models.fields.TextField', [], {}),
            'location_visible': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.TextField', [], {}),
            'name_visible': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'picture_url': ('django.db.models.fields.TextField', [], {}),
            'picture_url_visible': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        }
    }

    complete_apps = ['shared']