# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Picture'
        db.create_table(u'shared_picture', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('picture_id', self.gf('django.db.models.fields.TextField')(unique=True, db_index=True)),
            ('picture_filename', self.gf('django.db.models.fields.TextField')()),
            ('picture_data', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal(u'shared', ['Picture'])

        # Deleting field 'Profile.picture_url_visible'
        db.delete_column(u'shared_profile', 'picture_url_visible')

        # Deleting field 'Profile.picture_url'
        db.delete_column(u'shared_profile', 'picture_url')

        # Adding field 'Profile.picture_id'
        db.add_column(u'shared_profile', 'picture_id',
                      self.gf('django.db.models.fields.TextField')(default=''),
                      keep_default=False)

        # Adding field 'Profile.picture_visible'
        db.add_column(u'shared_profile', 'picture_visible',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting model 'Picture'
        db.delete_table(u'shared_picture')

        # Adding field 'Profile.picture_url_visible'
        db.add_column(u'shared_profile', 'picture_url_visible',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)

        # Adding field 'Profile.picture_url'
        db.add_column(u'shared_profile', 'picture_url',
                      self.gf('django.db.models.fields.TextField')(default=''),
                      keep_default=False)

        # Deleting field 'Profile.picture_id'
        db.delete_column(u'shared_profile', 'picture_id')

        # Deleting field 'Profile.picture_visible'
        db.delete_column(u'shared_profile', 'picture_visible')


    models = {
        u'shared.noncevalue': {
            'Meta': {'object_name': 'NonceValue'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'nonce': ('django.db.models.fields.TextField', [], {'unique': 'True', 'db_index': 'True'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {})
        },
        u'shared.picture': {
            'Meta': {'object_name': 'Picture'},
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