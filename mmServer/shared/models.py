""" mmServer.shared.models

    This module defines the shared database models used by the mmServer
    project.
"""
import datetime

from django.db   import models
from django.conf import settings

import django.utils.timezone
from django.db.models import Max

from mmServer.shared.lib import dbHelpers

#############################################################################

class ModelWithUpdateID(models.Model):
    """ A generic database model which saves records with a unique update ID.
    """
    update_id = models.IntegerField(unique=True, db_index=True, null=True)

    def save(self, *args, **kwargs):
        """ Save this record after calculating a new update_id value.

            We set the 'update_id' field to the current highest 'update_id'
            value in the database table, plus 1.  This indicates that this
            record has been updated.  The record is then saved into the
            database.
        """
        model = type(self)
        with dbHelpers.exclusive_access(model):
            max_value = model.objects.all().aggregate(Max('update_id'))
            if max_value['update_id__max'] == None:
                next_update_id = 1
            else:
                next_update_id = max_value['update_id__max'] + 1

            self.update_id = next_update_id
            super(ModelWithUpdateID, self).save(*args, **kwargs)


    class Meta:
        """ Metadata for our model.

            We tell Django that this should be an abstract base class.  This
            adds the 'update_id' field to our child model's database table.
        """
        abstract = True

#############################################################################

class Profile(ModelWithUpdateID):
    """ A User's profile.
    """
    id                                   = models.AutoField(primary_key=True)
    global_id                            = models.TextField(db_index=True,
                                                            unique=True)
    deleted                              = models.BooleanField(default=False)
    account_secret                       = models.TextField()
    name                                 = models.TextField(default="")
    name_visible                         = models.BooleanField(default=False)
    email                                = models.TextField(default="")
    phone                                = models.TextField(default="")
    address_1                            = models.TextField(default="")
    address_1_visible                    = models.BooleanField(default=False)
    address_2                            = models.TextField(default="")
    address_2_visible                    = models.BooleanField(default=False)
    city                                 = models.TextField(default="")
    city_visible                         = models.BooleanField(default=False)
    state_province_or_region             = models.TextField(default="")
    state_province_or_region_visible     = models.BooleanField(default=False)
    zip_or_postal_code                   = models.TextField(default="")
    zip_or_postal_code_visible           = models.BooleanField(default=False)
    country                              = models.TextField(default="")
    country_visible                      = models.BooleanField(default=False)
    date_of_birth                        = models.DateField(null=True)
    social_security_number_last_4_digits = models.TextField(default="")
    bio                                  = models.TextField(default="")
    bio_visible                          = models.BooleanField(default=False)
    picture_id                           = models.TextField(default="")
    picture_id_visible                   = models.BooleanField(default=False)

#############################################################################

class Picture(ModelWithUpdateID):
    """ An uploaded picture.

        Note that the 'picture_data' field holds the image data in base64
        encoding.
    """
    id               = models.AutoField(primary_key=True)
    picture_id       = models.TextField(db_index=True, unique=True)
    deleted          = models.BooleanField(default=False)
    account_secret   = models.TextField()
    picture_filename = models.TextField()
    picture_data     = models.TextField()

#############################################################################

class Conversation(ModelWithUpdateID):
    """ A conversation between two users.
    """
    id              = models.AutoField(primary_key=True)
    global_id_1    = models.TextField(db_index=True)
    global_id_2    = models.TextField(db_index=True)
    encryption_key = models.TextField()
    hidden_1       = models.BooleanField(default=False)
    hidden_2       = models.BooleanField(default=False)
    last_message_1 = models.TextField(null=True)
    last_message_2 = models.TextField(null=True)
    last_timestamp = models.DateTimeField(null=True)
    num_unread_1   = models.IntegerField()
    num_unread_2   = models.IntegerField()


    class Meta:
        unique_together = ("global_id_1", "global_id_2")

#############################################################################

class Message(ModelWithUpdateID):
    """ A message sent between two users.
    """
    STATUS_PENDING = 0
    STATUS_SENT    = 2
    STATUS_READ    = 3
    STATUS_FAILED  = -1

    STATUS_CHOICES = ((STATUS_PENDING, "PENDING"),
                      (STATUS_SENT,    "SENT"),
                      (STATUS_READ,    "READ"),
                      (STATUS_FAILED,  "FAILED"))

    STATUS_MAP = {STATUS_PENDING : "PENDING",
                  STATUS_SENT    : "SENT",
                  STATUS_READ    : "READ",
                  STATUS_FAILED  : "FAILED"}

    id                   = models.AutoField(primary_key=True)
    conversation         = models.ForeignKey(Conversation)
    hash                 = models.TextField(null=True, db_index=True)
    timestamp            = models.DateTimeField()
    sender_global_id     = models.TextField(db_index=True)
    recipient_global_id  = models.TextField(db_index=True)
    sender_account_id    = models.TextField()
    recipient_account_id = models.TextField()
    sender_text          = models.TextField()
    recipient_text       = models.TextField()
    action               = models.TextField(null=True)
    action_params        = models.TextField(null=True)
    action_processed     = models.BooleanField(default=False)
    system_charge        = models.IntegerField(default=0)
    recipient_charge     = models.IntegerField(default=0)
    status               = models.IntegerField(choices=STATUS_CHOICES,
                                               db_index=True)
    error                = models.TextField(null=True)

#############################################################################

class Account(models.Model):
    """ A user's MessageMe account.
    """
    TYPE_USER           = "U"
    TYPE_MESSAGEME      = "M"
    TYPE_RIPPLE_HOLDING = "R"

    TYPE_CHOICES = ((TYPE_USER,           "USER"),
                    (TYPE_MESSAGEME,      "MESSAGEME"),
                    (TYPE_RIPPLE_HOLDING, "RIPPLE_HOLDING"))

    TYPE_MAP = {TYPE_USER           : "USER",
                TYPE_MESSAGEME      : "MESSAGEME",
                TYPE_RIPPLE_HOLDING : "RIPPLE_HOLDING"}

    id               = models.AutoField(primary_key=True)
    type             = models.CharField(max_length=1, choices=TYPE_CHOICES,
                                        db_index=True)
    global_id        = models.TextField(null=True, db_index=True, unique=True)
    balance_in_drops = models.IntegerField()

#############################################################################

class Transaction(models.Model):
    """ A single transaction against a user's MessageMe account.
    """
    STATUS_PENDING = 0
    STATUS_SUCCESS = 1
    STATUS_FAILED  = 2

    STATUS_CHOICES = ((STATUS_PENDING, "PENDING"),
                      (STATUS_SUCCESS, "SUCCESS"),
                      (STATUS_FAILED,  "FAILED"))

    STATUS_MAP = {STATUS_PENDING : "PENDING",
                  STATUS_SUCCESS : "SUCCESS",
                  STATUS_FAILED  : "FAILED"}

    TYPE_DEPOSIT          = "D"
    TYPE_WITHDRAWAL       = "W"
    TYPE_SYSTEM_CHARGE    = "S"
    TYPE_RECIPIENT_CHARGE = "R"
    TYPE_ADJUSTMENT       = "A"

    TYPE_CHOICES = ((TYPE_DEPOSIT,          "DEPOSIT"),
                    (TYPE_WITHDRAWAL,       "WITHDRAWAL"),
                    (TYPE_SYSTEM_CHARGE,    "SYSTEM_CHARGE"),
                    (TYPE_RECIPIENT_CHARGE, "RECIPIENT_CHARGE"),
                    (TYPE_ADJUSTMENT,       "ADJUSTMENT"))

    TYPE_MAP = {TYPE_DEPOSIT          : "DEPOSIT",
                TYPE_WITHDRAWAL       : "WITHDRAWAL",
                TYPE_SYSTEM_CHARGE    : "SYSTEM_CHARGE",
                TYPE_RECIPIENT_CHARGE : "RECIPIENT_CHARGE",
                TYPE_ADJUSTMENT       : "ADJUSTMENT"}

    id                      = models.AutoField(primary_key=True)
    timestamp               = models.DateTimeField(db_index=True)
    created_by              = models.ForeignKey(Account,
                                      related_name="transactions_created_by_me")
    status                  = models.IntegerField(choices=STATUS_CHOICES,
                                                  db_index=True)
    type                    = models.CharField(max_length=1,
                                               choices=TYPE_CHOICES,
                                               db_index=True)
    amount_in_drops         = models.IntegerField()
    debit_account           = models.ForeignKey(Account,
                                       related_name="debit_transactions")
    credit_account          = models.ForeignKey(Account,
                                       related_name="credit_transactions")
    ripple_transaction_hash = models.TextField(null=True)
    message_hash            = models.TextField(null=True)
    description             = models.TextField(null=True)
    error                   = models.TextField(null=True)

#############################################################################

class NonceValueManager(models.Manager):
    """ A custom manager for the NonceValue database table.
    """
    def purge(self):
        """ Delete all NonceValues older than settings.KEEP_NONCE_VALUES_FOR.
        """
        if settings.KEEP_NONCE_VALUES_FOR == None:
            return # Keep Nonce values forever.

        max_age = datetime.timedelta(days=settings.KEEP_NONCE_VALUES_FOR)
        cutoff  = django.utils.timezone.now() - max_age

        self.filter(timestamp__lte=cutoff).delete()

#############################################################################

class NonceValue(models.Model):
    """ A Nonce value that has been used to make an authenticated request.

        Note that we timestamp the Nonce values.  We delete old Nonce values to
        keep this database table to a reasonable size; the exact length of time
        we keep the Nonce values depends on a custom setting; a period needs to
        be long enough to ensure that HMAC-authenticated requests cannot be
        resent.  A period of a year is probably a good value.
    """
    id        = models.AutoField(primary_key=True)
    nonce     = models.TextField(db_index=True, unique=True)
    timestamp = models.DateTimeField()

    # Use our custom manager for the NonceValue class.

    objects = NonceValueManager()

