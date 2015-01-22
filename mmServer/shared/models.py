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

class Profile(models.Model):
    """ A User's profile.
    """
    global_id        = models.TextField(db_index=True, unique=True)
    account_secret   = models.TextField()
    name             = models.TextField()
    name_visible     = models.BooleanField(default=False)
    location         = models.TextField()
    location_visible = models.BooleanField(default=False)
    picture_id       = models.TextField()
    picture_visible  = models.BooleanField(default=False)

#############################################################################

class Picture(models.Model):
    """ An uploaded picture.

        Note that the 'picture_data' field holds the image data in base64
        encoding.
    """
    picture_id       = models.TextField(db_index=True, unique=True)
    account_secret   = models.TextField()
    picture_filename = models.TextField()
    picture_data     = models.TextField()

#############################################################################

class Conversation(models.Model):
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

class Message(models.Model):
    """ A message sent between two users.

        Note that the 'update_id' field is used to let callers poll for new and
        updated messages.  This field should be incremented each time a message
        is added or updated.
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

    update_id            = models.IntegerField(unique=True, db_index=True)
    conversation         = models.ForeignKey(Conversation)
    hash                 = models.TextField(null=True, db_index=True)
    timestamp            = models.DateTimeField()
    sender_global_id     = models.TextField()
    recipient_global_id  = models.TextField()
    sender_account_id    = models.TextField()
    recipient_account_id = models.TextField()
    text                 = models.TextField()
    status               = models.IntegerField(choices=STATUS_CHOICES,
                                               db_index=True)
    error                = models.TextField(null=True)


    def save_with_new_update_id(self):
        """ Save this message after calculating a new update_id value.

            We set the 'update_id' field to the current highest 'update_id' value
            in the Message table, plus 1.  This indicates that this message has
            been updated.  The Message record is then saved into the database.
        """
        with dbHelpers.exclusive_access(Message):
            max_value = Message.objects.all().aggregate(Max('update_id'))
            if max_value['update_id__max'] == None:
                next_update_id = 1
            else:
                next_update_id = max_value['update_id__max'] + 1

            self.update_id = next_update_id
            self.save()

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

