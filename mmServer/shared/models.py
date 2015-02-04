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
    global_id        = models.TextField(db_index=True, unique=True)
    deleted          = models.BooleanField(default=False)
    account_secret   = models.TextField()
    name             = models.TextField()
    name_visible     = models.BooleanField(default=False)
    location         = models.TextField()
    location_visible = models.BooleanField(default=False)
    picture_id       = models.TextField()
    picture_visible  = models.BooleanField(default=False)

#############################################################################

class Picture(ModelWithUpdateID):
    """ An uploaded picture.

        Note that the 'picture_data' field holds the image data in base64
        encoding.
    """
    picture_id       = models.TextField(db_index=True, unique=True)
    deleted          = models.BooleanField(default=False)
    account_secret   = models.TextField()
    picture_filename = models.TextField()
    picture_data     = models.TextField()

#############################################################################

class Conversation(ModelWithUpdateID):
    """ A conversation between two users.
    """
    global_id_1    = models.TextField(db_index=True)
    global_id_2    = models.TextField(db_index=True)
    encryption_key = models.TextField()
    hidden_1       = models.BooleanField(default=False)
    hidden_2       = models.BooleanField(default=False)
    last_message   = models.TextField(null=True)
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

    conversation         = models.ForeignKey(Conversation)
    hash                 = models.TextField(null=True, db_index=True)
    timestamp            = models.DateTimeField()
    sender_global_id     = models.TextField()
    recipient_global_id  = models.TextField()
    sender_account_id    = models.TextField()
    recipient_account_id = models.TextField()
    text                 = models.TextField()
    action               = models.TextField(null=True)
    action_params        = models.TextField(null=True)
    action_processed     = models.BooleanField(default=False)
    amount_in_drops      = models.IntegerField(default=1)
    status               = models.IntegerField(choices=STATUS_CHOICES,
                                               db_index=True)
    error                = models.TextField(null=True)

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
    nonce     = models.TextField(db_index=True, unique=True)
    timestamp = models.DateTimeField()

    # Use our custom manager for the NonceValue class.

    objects = NonceValueManager()

