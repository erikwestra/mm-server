# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models

class Migration(DataMigration):

    def forwards(self, orm):
        """ Create 'message' ForeignKey relation out of the message_hash field.
        """
        for transaction in orm.Transaction.objects.all():
            msg_hash = transaction.message_hash
            if msg_hash != None:
                try:
                    message = orm.Message.objects.get(hash=msg_hash)
                except orm.Message.DoesNotExist:
                    continue
                transaction.message = message
                transaction.save()


    def backwards(self, orm):
        """ Remove the contents of the 'message' ForeignKey relation.
        """
        for transaction in orm.Transaction.objects.all():
            transaction.message = None
            transaction.save()


    models = {
        u'shared.account': {
            'Meta': {'object_name': 'Account'},
            'balance_in_drops': ('django.db.models.fields.IntegerField', [], {}),
            'global_id': ('django.db.models.fields.TextField', [], {'unique': 'True', 'null': 'True', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '1', 'db_index': 'True'})
        },
        u'shared.conversation': {
            'Meta': {'unique_together': "(('global_id_1', 'global_id_2'),)", 'object_name': 'Conversation'},
            'encryption_key': ('django.db.models.fields.TextField', [], {}),
            'global_id_1': ('django.db.models.fields.TextField', [], {'db_index': 'True'}),
            'global_id_2': ('django.db.models.fields.TextField', [], {'db_index': 'True'}),
            'hidden_1': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'hidden_2': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
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
            'conversation': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['shared.Conversation']"}),
            'error': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'hash': ('django.db.models.fields.TextField', [], {'null': 'True', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'recipient_account_id': ('django.db.models.fields.TextField', [], {}),
            'recipient_charge': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'recipient_global_id': ('django.db.models.fields.TextField', [], {'db_index': 'True'}),
            'recipient_text': ('django.db.models.fields.TextField', [], {}),
            'sender_account_id': ('django.db.models.fields.TextField', [], {}),
            'sender_global_id': ('django.db.models.fields.TextField', [], {'db_index': 'True'}),
            'sender_text': ('django.db.models.fields.TextField', [], {}),
            'status': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'system_charge': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {}),
            'update_id': ('django.db.models.fields.IntegerField', [], {'unique': 'True', 'null': 'True', 'db_index': 'True'})
        },
        u'shared.noncevalue': {
            'Meta': {'object_name': 'NonceValue'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'nonce': ('django.db.models.fields.TextField', [], {'unique': 'True', 'db_index': 'True'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {})
        },
        u'shared.picture': {
            'Meta': {'object_name': 'Picture'},
            'account_secret': ('django.db.models.fields.TextField', [], {}),
            'deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
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
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
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
        },
        u'shared.transaction': {
            'Meta': {'object_name': 'Transaction'},
            'amount_in_drops': ('django.db.models.fields.IntegerField', [], {}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'transactions_created_by_me'", 'to': u"orm['shared.Account']"}),
            'credit_account': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'credit_transactions'", 'to': u"orm['shared.Account']"}),
            'debit_account': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'debit_transactions'", 'to': u"orm['shared.Account']"}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'error': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['shared.Message']", 'null': 'True'}),
            'message_hash': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'ripple_transaction_hash': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'status': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '1', 'db_index': 'True'})
        }
    }

    complete_apps = ['shared']
    symmetrical = True