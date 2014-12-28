# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Profile'
        db.create_table(u'shared_profile', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('global_id', self.gf('django.db.models.fields.TextField')(unique=True, db_index=True)),
            ('name', self.gf('django.db.models.fields.TextField')()),
            ('location', self.gf('django.db.models.fields.TextField')()),
            ('image_url', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal(u'shared', ['Profile'])


    def backwards(self, orm):
        # Deleting model 'Profile'
        db.delete_table(u'shared_profile')


    models = {
        u'shared.profile': {
            'Meta': {'object_name': 'Profile'},
            'global_id': ('django.db.models.fields.TextField', [], {'unique': 'True', 'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image_url': ('django.db.models.fields.TextField', [], {}),
            'location': ('django.db.models.fields.TextField', [], {}),
            'name': ('django.db.models.fields.TextField', [], {})
        }
    }

    complete_apps = ['shared']