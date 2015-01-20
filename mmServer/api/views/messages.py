""" mmServer.api.views.messages

    This module implements the "messages" endpoint for the mmServer.api
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

#############################################################################

logger = logging.getLogger(__name__)

#############################################################################

@csrf_exempt
def endpoint(request):
    """ Respond to the "/api/messages" endpoint.

        This view function simply selects an appropriate handler based on the
        HTTP method.
    """
    if request.method == "GET":
        return messages_GET(request)
    else:
        return HttpResponseNotAllowed(["GET"])

#############################################################################

def messages_GET(request):
    """ Respond to the "GET /api/messages" API request.

        This is used to retrieve a list of messages for a given pair of users.
    """
    if not utils.has_hmac_headers(request):
        return HttpResponseForbidden()

    if "my_global_id" in request.GET:
        my_global_id = request.GET['my_global_id']
    else:
        return HttpResponseBadRequest("Missing 'my_global_id' parameter.")

    if "their_global_id" in request.GET:
        their_global_id = request.GET['their_global_id']
    else:
        return HttpResponseBadRequest("Missing 'their_global_id' parameter.")

    if "anchor" in request.GET:
        anchor = request.GET['anchor']
    else:
        anchor = None

    try:
        my_profile = Profile.objects.get(global_id=my_global_id)
    except Profile.DoesNotExist:
        return HttpResponseBadRequest("User doesn't have a profile!")

    if not utils.check_hmac_authentication(request,
                                           my_profile.account_secret):
        return HttpResponseForbidden()

    # Get the Conversation for these two users.  If there is no Conversation
    # record for these two users, return a empty response as there won't be any
    # messages.

    try:
        conversation = Conversation.objects.get(global_id_1=my_global_id,
                                                global_id_2=their_global_id)
    except Conversation.DoesNotExist:
        try:
            conversation = Conversation.objects.get(global_id_1=their_global_id,
                                                    global_id_2=my_global_id)
        except Conversation.DoesNotExist:
            conversation = None

    if conversation == None:
        return HttpResponse(json.dumps({'messages'    : [],
                                        'next_anchor' : ""}),
                            mimetype="application/json")

    # See if we have any pending messages for this conversation.  If so, ask
    # the Ripple network for the current status of these messages, and finalize
    # any that have either failed or been accepted into the Ripple ledger.

    cutoff = timezone.now() - datetime.timedelta(seconds=30)

    msgs_to_check = []
    for message in PendingMessage.objects.all():
        if message.last_status_check == None:
            msgs_to_check.append(message)
        elif message.last_status_check < cutoff:
            msgs_to_check.append(message)

    for msg in msgs_to_check:
        response = rippleInterface.request("tx", transaction=msg.hash,
                                                 binary=False)
        if response == None:
            continue

        if response['status'] != "success":
            logger.warn("Ripple server returned error: " + repr(response))
            continue

        if response['result'].get("validated", False):
            # This message has been validated -> finalize it.
            trans_result = response['result']['meta']['TransactionResult']

            final = FinalMessage()
            final.conversation         = msg.conversation
            final.hash                 = msg.hash
            final.timestamp            = msg.timestamp
            final.sender_global_id     = msg.sender_global_id
            final.recipient_global_id  = msg.recipient_global_id
            final.sender_account_id    = msg.sender_account_id
            final.recipient_account_id = msg.recipient_account_id
            final.text                 = msg.text

            if trans_result == "tesSUCCESS":
                final.error = None
            else:
                final.error = trans_result

            final.save()
            msg.delete()

    # Collect the finalised messages for this conversation.

    messages = []

    query = FinalMessage.objects.filter(conversation=conversation)
    if anchor != None:
        query = query.filter(id__gt=anchor)

    for msg in query.order_by("id"):

        if msg.error != None and msg.sender_global_id != my_global_id:
            pass # Exclude failed messages sent by the other party.

        timestamp = utils.datetime_to_unix_timestamp(msg.timestamp)

        messages.append({'hash'                 : msg.hash,
                         'timestamp'            : timestamp,
                         'sender_global_id'     : msg.sender_global_id,
                         'recipient_global_id'  : msg.recipient_global_id,
                         'sender_account_id'    : msg.sender_account_id,
                         'recipient_account_id' : msg.recipient_account_id,
                         'text'                 : msg.text})
        if msg.error:
            messages[-1]['error'] = msg.error

    # Calculate the next_anchor value.

    next_anchor = None # initially.
    for msg in FinalMessage.objects.order_by("-id"):
        next_anchor = str(msg.id)
        break

    # Finally, return the results back to the caller.

    return HttpResponse(json.dumps({'messages'    : messages,
                                    'next_anchor' : next_anchor}),
                        mimetype="application/json")

