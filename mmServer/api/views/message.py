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
from mmServer.shared.lib    import messageHandler

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

    if "amount_in_drops" in data:
        amount_in_drops = data['amount_in_drops']
    else:
        amount_in_drops = 1 # Hardwired default.

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

    # Encrypt the message using the conversation's encryption key.

    encrypted_message = encryption.encrypt(conversation.encryption_key,
                                           recipient_text)

    # Create the Ripple transaction to be sent.

    memos = []
    memos.append({'Memo' : {
                    'MemoType' : encryption.hex_encode("MM_VERSION"),
                    'MemoData' : encryption.hex_encode("1")}}) # Hardwired.
    memos.append({'Memo' : {
                    'MemoType' : encryption.hex_encode("MM_MESSAGE"),
                    'MemoData' : encryption.hex_encode(encrypted_message)}})

    transaction = {'TransactionType' : "Payment",
                   'Account'         : sender_account_id,
                   'Destination'     : recipient_account_id,
                   'Amount'          : str(amount_in_drops),
                   'Memos'           : memos
                  }

    # Ask the Ripple network to sign our message, using the sending user's
    # account secret.

    error = None # initially.

    response = rippleInterface.request("sign",
                                       tx_json=transaction,
                                       secret=senders_profile.account_secret,
                                       fee_mult_max=1000000)
    if response == None:
        error = "Ripple server failed to respond when signing the transaction"
    elif response['status'] != "success":
        error = "Ripple server error signing transaction: " + response['error']

    # Now attempt to submit the transaction to the Ripple ledger.

    if error == None:
        tx_blob = response['result']['tx_blob']

        response = rippleInterface.request("submit",
                                           tx_blob=tx_blob,
                                           fail_hard=True)

        if response == None:
            error = "Ripple server failed to respond when submitting " \
                  + "transaction"
        elif response['status'] != "success":
            error = "Ripple server error submittting transaction: " \
                  + response['error']

    # If there's an error, tell the user about it.

    if error != None:
        return HttpResponseBadRequest(error)

    # Finally, create the new Message object and tell the user the good news.

    message = Message()
    message.conversation         = conversation
    message.hash                 = response['result']['tx_json']['hash']
    message.timestamp            = timezone.now()
    message.sender_global_id     = sender_global_id
    message.recipient_global_id  = recipient_global_id
    message.sender_account_id    = sender_account_id
    message.recipient_account_id = recipient_account_id
    message.sender_text          = sender_text
    message.recipient_text       = recipient_text
    message.action               = action
    message.action_params        = action_params
    message.status               = Message.STATUS_PENDING
    message.amount_in_drops      = amount_in_drops
    message.error                = None
    message.save()

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

