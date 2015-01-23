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
from django.db.models             import Max

import simplejson as json

from mmServer.shared.models import *
from mmServer.shared.lib    import rippleInterface, encryption
from mmServer.shared.lib    import utils, dbHelpers

#############################################################################

logger = logging.getLogger(__name__)

#############################################################################

@csrf_exempt
def endpoint(request):
    """ Respond to the "/api/messages" endpoint.

        This view function simply selects an appropriate handler based on the
        HTTP method.
    """
    try:
        if request.method == "GET":
            return messages_GET(request)
        else:
            return HttpResponseNotAllowed(["GET"])
    except:
        return utils.exception_response()

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

    msgs_to_check = []
    for msg in Message.objects.filter(status=Message.STATUS_PENDING):
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
            if trans_result == "tesSUCCESS":
                msg.status = Message.STATUS_SENT
                msg.error  = None
            else:
                msg.status  = Message.STATUS_FAILED
                final.error = trans_result
            msg.save_with_new_update_id()

    # Perform the actual grabbing of the data with an exclusive table lock.
    # This prevents other clients from changing the data until we're finished.

    with dbHelpers.exclusive_access(Message):
        # Go through the list of messages we want to download, and mark any
        # messages sent to the current user as "read".  Note that this will
        # alter the update_id for these messages, so we have to do this before
        # we collect the final list of messages to return to the caller.

        query = Message.objects.filter(conversation=conversation)
        if anchor not in[None, ""]:
            query = query.filter(update_id__gt=anchor)

        found_messages = []
        for msg in query:
            found_messages.append(msg)

        for msg in found_messages:
            if ((msg.recipient_global_id == my_global_id) and
                (msg.status == Message.STATUS_SENT)):
                msg.status = Message.STATUS_READ
                msg.save_with_new_update_id()

        # Now collect the list of messages for this conversation.  If the
        # caller provided an anchor, we only collect the new and updated
        # messages since the last time this endpoint was called.

        query = Message.objects.filter(conversation=conversation)
        if anchor not in[None, ""]:
            query = query.filter(update_id__gt=anchor)

        messages = []
        for msg in query.order_by("id"):
            timestamp = utils.datetime_to_unix_timestamp(msg.timestamp)
            status    = Message.STATUS_MAP[msg.status]

            messages.append({'hash'                 : msg.hash,
                             'timestamp'            : timestamp,
                             'sender_global_id'     : msg.sender_global_id,
                             'recipient_global_id'  : msg.recipient_global_id,
                             'sender_account_id'    : msg.sender_account_id,
                             'recipient_account_id' : msg.recipient_account_id,
                             'text'                 : msg.text,
                             'status'               : status})
            if msg.error:
                messages[-1]['error'] = msg.error

        # Calculate the next anchor value to use.

        max_value = Message.objects.all().aggregate(Max('update_id'))
        if max_value['update_id__max'] == None:
            next_anchor = ""
        else:
            next_anchor = str(max_value['update_id__max'])

    # Finally, return the results back to the caller.

    return HttpResponse(json.dumps({'messages'    : messages,
                                    'next_anchor' : next_anchor}),
                        mimetype="application/json")

