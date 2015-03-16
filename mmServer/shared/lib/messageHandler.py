""" mmServer.shared.lib.messageHandler

    This module define various functions which work with messages.
"""
import datetime
import logging

from django.utils import timezone

from mmServer.shared.lib    import rippleInterface
from mmServer.shared.models import *

#############################################################################

logger = logging.getLogger("mmServer")

#############################################################################

def check_pending_messages():
    """ Check any messages with a status of "pending".

        We ask the Ripple network for the current status of each of "pending"
        message, and update the status for any message that has either failed
        or been accepted into the Ripple ledger.

        If a message was accepted, the associated conversation will also be
        updated to reflect the current unread message count and the details of
        the latest message.
    """
    conversations_to_update = set()

    for msg in Message.objects.filter(status=Message.STATUS_PENDING):
        response = rippleInterface.request("tx", transaction=msg.hash,
                                                 binary=False)
        if response == None:
            continue

        if response['status'] == "error":
            # The Ripple server returned an error.  If the error was
            # "txnNotFound" and the message is more than 60 seconds old, mark
            # it as failed so we don't continue to check for failed messages.
            cutoff = timezone.now() - datetime.timedelta(seconds=60)
            if response['error'] == "txnNotFound" and msg.timestamp < cutoff:
                msg.status = Message.STATUS_FAILED
                msg.error  = response['error']
                msg.save()
                continue

        if response['result'].get("validated", False):
            # This message has been validated -> update the status.

            trans_result = response['result']['meta']['TransactionResult']
            if trans_result == "tesSUCCESS":
                msg.status = Message.STATUS_SENT
                msg.error  = None
            else:
                msg.status  = Message.STATUS_FAILED
                msg.error = trans_result
            msg.save()

            # If the message was sent, update the conversation this message is
            # part of.  This updates the unread message count, etc, for the
            # conversation.

            if msg.status == Message.STATUS_SENT:
                conversations_to_update.add(msg.conversation)

    for conversation in conversations_to_update:
        update_conversation(conversation)

#############################################################################

def update_conversation(conversation):
    """ Update a conversation to reflect the current state of its messages.

        We update the following fields in the Conversation record to reflect
        the current set of messages associated with that conversation:

            last_message
            last_timestamp
            num_unread_1
            num_unread_2
    """
    conversation.num_unread_1 = 0
    conversation.num_unread_2 = 0

    for message in Message.objects.filter(conversation=conversation):
        if ((conversation.last_timestamp == None) or
            (message.timestamp > conversation.last_timestamp)):
            if conversation.global_id_1 == message.sender_global_id:
                conversation.last_message_1 = message.sender_text
                conversation.last_message_2 = message.recipient_text
            else:
                conversation.last_message_1 = message.recipient_text
                conversation.last_message_2 = message.sender_text
            conversation.last_timestamp = message.timestamp

        if message.status == Message.STATUS_SENT:
            if message.sender_global_id == conversation.global_id_1:
                conversation.num_unread_2 = conversation.num_unread_2 + 1
            else:
                conversation.num_unread_1 = conversation.num_unread_1 + 1

    conversation.save()

