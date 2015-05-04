""" mmServer.api.views.message

    This module implements the "message" endpoint for the mmServer.api
    application.
"""
import base64
import logging
import os.path
import uuid

from django.http                  import *
from django.views.decorators.csrf import csrf_exempt
from django.utils                 import timezone

import simplejson as json

from mmServer.shared.models import *
from mmServer.shared.lib    import utils, rippleInterface, encryption
from mmServer.shared.lib    import messageHandler, transactionHandler

#############################################################################

logger = logging.getLogger(__name__)

#############################################################################

@csrf_exempt
def endpoint(request):
    """ Respond to the "/api/message" endpoint.

        This view function simply selects an appropriate handler based on the
        HTTP method.
    """
    try:
        if request.method == "POST":
            return message_POST(request)
        elif request.method == "PUT":
            return message_PUT(request)
        else:
            return HttpResponseNotAllowed(["POST", 'PUT'])
    except:
        return utils.exception_response()

#############################################################################

def message_POST(request):
    """ Respond to the "POST /api/message" API request.

        This is used to send a message.
    """
    if not utils.has_hmac_headers(request):
        return HttpResponseForbidden()

    if request.META['CONTENT_TYPE'] != "application/json":
        return HttpResponseBadRequest("Request must be in JSON format.")

    data = json.loads(request.body)

    if "sender_global_id" not in data:
        return HttpResponseBadRequest("Missing 'sender_global_id' field.")
    else:
        sender_global_id = data['sender_global_id']

    if "recipient_global_id" not in data:
        return HttpResponseBadRequest("Missing 'recipient_global_id' field.")
    else:
        recipient_global_id = data['recipient_global_id']

    if "sender_account_id" not in data:
        return HttpResponseBadRequest("Missing 'sender_account_id' field.")
    else:
        sender_account_id = data['sender_account_id']

    if "recipient_account_id" not in data:
        return HttpResponseBadRequest("Missing 'recipient_account_id' field.")
    else:
        recipient_account_id = data['recipient_account_id']

    if "sender_text" not in data:
        return HttpResponseBadRequest("Missing 'sender_text' field.")
    else:
        sender_text = data['sender_text']

    if "recipient_text" not in data:
        return HttpResponseBadRequest("Missing 'recipient_text' field.")
    else:
        recipient_text = data['recipient_text']

    if "action" in data:
        action = data['action']
    else:
        action = None

    if "action_params" in data:
        action_params = data['action_params']
    else:
        action_params = None

    if "system_charge" not in data:
        return HttpResponseBadRequest("Missing 'system_charge' field.")
    else:
        system_charge = data['system_charge']

    if "recipient_charge" not in data:
        return HttpResponseBadRequest("Missing 'recipient_charge' field.")
    else:
        recipient_charge = data['recipient_charge']

    try:
        senders_profile = Profile.objects.get(global_id=sender_global_id)
    except Profile.DoesNotExist:
        return HttpResponseBadRequest("The sender doesn't have a profile!")

    if not utils.check_hmac_authentication(request,
                                           senders_profile.account_secret):
        return HttpResponseForbidden()

    # Get the Conversation for these two users.  If there is no Conversation
    # record for these two users, create one now.

    try:
        conversation = Conversation.objects.get(global_id_1=sender_global_id,
                                                global_id_2=recipient_global_id)
    except Conversation.DoesNotExist:
        try:
            conversation = Conversation.objects.get(
                                    global_id_1=recipient_global_id,
                                    global_id_2=sender_global_id)
        except Conversation.DoesNotExist:
            conversation = None

    if conversation == None:
        conversation = Conversation()
        conversation.global_id_1    = sender_global_id
        conversation.global_id_2    = recipient_global_id
        conversation.encryption_key = encryption.generate_random_key()
        conversation.hidden_1       = False
        conversation.hidden_2       = False
        conversation.last_message_1 = None
        conversation.last_message_2 = None
        conversation.last_timestamp = None
        conversation.num_unread_1   = 0
        conversation.num_unread_2   = 0
        conversation.save()

    # Withdraw the transaction fees from the user's account.  If they don't
    # have enough funds to cover the fees, reject the message.

    transactions = []

    with dbHelpers.exclusive_access(Account, Transaction):

        # Get the sender's account, creating it if necessary.

        try:
            sender_account = Account.objects.get(type=Account.TYPE_USER,
                                                 global_id=sender_global_id)
        except Account.DoesNotExist:
            sender_account = Account()
            sender_account.type             = Account.TYPE_USER
            sender_account.global_id        = sender_global_id
            sender_account.balance_in_drops = 0
            sender_account.save()

        # If the sender doesn't have enough money in their account, reject the
        # message.

        if sender_account.balance_in_drops < system_charge + recipient_charge:
            return HttpResponse(status=402) # 402 = Payment required.

        if recipient_charge > 0:

            # Get the recipient's account, creating it if necessary.

            try:
                recipient_account = Account.objects.get(
                                                type=Account.TYPE_USER,
                                                global_id=recipient_global_id)
            except Account.DoesNotExist:
                recipient_account = Account()
                recipient_account.type             = Account.TYPE_USER
                recipient_account.global_id        = recipient_global_id
                recipient_account.balance_in_drops = 0
                recipient_account.save()

            # Create a transaction deducting the recipient charge from the
            # sender's account.

            t = Transaction()
            t.timestamp               = timezone.now()
            t.created_by              = sender_account
            t.status                  = Transaction.STATUS_SUCCESS
            t.type                    = Transaction.TYPE_RECIPIENT_CHARGE
            t.amount_in_drops         = recipient_charge
            t.debit_account           = sender_account
            t.credit_account          = recipient_account
            t.ripple_transaction_hash = None
            t.message                 = None
            t.description             = None
            t.error                   = None
            t.save()

            transactions.append(t)

            # Update the recipient's account balance.

            transactionHandler.update_account_balance(recipient_account)

        if system_charge > 0:

            # Get the MessageMe system account, creating it if necessary.

            try:
                system_account = Account.objects.get(type=Account.TYPE_MESSAGEME)
            except Account.DoesNotExist:
                system_account = Account()
                system_account.type             = Account.TYPE_MESSAGEME
                system_account.global_id        = None
                system_account.balance_in_drops = 0
                system_account.save()

            # Create a transaction deducting the system charge from the
            # sender's account.

            t = Transaction()
            t.timestamp               = timezone.now()
            t.created_by              = sender_account
            t.status                  = Transaction.STATUS_SUCCESS
            t.type                    = Transaction.TYPE_SYSTEM_CHARGE
            t.amount_in_drops         = system_charge
            t.debit_account           = sender_account
            t.credit_account          = system_account
            t.ripple_transaction_hash = None
            t.message                 = None
            t.description             = None
            t.error                   = None
            t.save()

            transactions.append(t)

            # Update the MessageMe system account balance.

            transactionHandler.update_account_balance(system_account)

        # Update the sender's account balance.

        if recipient_charge > 0 or system_charge > 0:
            transactionHandler.update_account_balance(sender_account)

    # Create the new Message object.  Note that the message is marked as "SENT"
    # right away.

    message = Message()
    message.conversation         = conversation
    message.hash                 = uuid.uuid4().hex
    message.timestamp            = timezone.now()
    message.sender_global_id     = sender_global_id
    message.recipient_global_id  = recipient_global_id
    message.sender_account_id    = sender_account_id
    message.recipient_account_id = recipient_account_id
    message.sender_text          = sender_text
    message.recipient_text       = recipient_text
    message.action               = action
    message.action_params        = action_params
    message.system_charge        = system_charge
    message.recipient_charge     = recipient_charge
    message.status               = Message.STATUS_SENT
    message.error                = None
    message.save()

    # Update the underlying conversation.

    messageHandler.update_conversation(conversation)

    # Link the charge transactions back to the message, now that we've created
    # it.

    for transaction in transactions:
        transaction.message = message
        transaction.save()

    # Finally, tell the caller the good news.

    return HttpResponse(status=202)

#############################################################################

def message_PUT(request):
    """ Respond to the "PUT /api/message" API request.

        This is used to update a message.
    """
    # Process our parameters.

    if not utils.has_hmac_headers(request):
        return HttpResponseForbidden()

    if request.META['CONTENT_TYPE'] != "application/json":
        return HttpResponseBadRequest("Request must be in JSON format.")

    data = json.loads(request.body)

    if "message" not in data:
        return HttpResponseBadRequest("Missing 'message' field.")

    if "hash" not in data['message']:
        return HttpResponseBadRequest("Missing 'hash' field.")
    else:
        hash = data['message']['hash']

    if "processed" in data['message']:
        processed = (data['message']['processed'] == True)
    else:
        processed = False

    if "read" in data['message']:
        read = (data['message']['read'] == True)
    else:
        read = False

    # Find the message to update.

    try:
        message = Message.objects.get(hash=hash)
    except Message.DoesNotExist:
        return HttpResponseNotFound()

    # Check that the recipient is the one trying to update the message.

    try:
        recipients_profile = Profile.objects.get(
                                        global_id=message.recipient_global_id)
    except Profile.DoesNotExist:
        return HttpResponseBadRequest("The recipient doesn't have a profile!")

    if not utils.check_hmac_authentication(request,
                                           recipients_profile.account_secret):
        return HttpResponseForbidden()

    # We're good to go.  Update the message.

    if processed: message.action_processed = True
    if read:      message.status           = Message.STATUS_READ
    message.save()

    # Finally, update the underlying conversation if appropriate.

    if read:
        messageHandler.update_conversation(message.conversation)

    return HttpResponse(status=200)

