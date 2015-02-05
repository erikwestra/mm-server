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
from django.db.models             import Max, Q

import simplejson as json

from mmServer.shared.models import *
from mmServer.shared.lib    import rippleInterface, encryption
from mmServer.shared.lib    import utils, dbHelpers, messageHandler

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
        their_global_id = None

    try:
        my_profile = Profile.objects.get(global_id=my_global_id)
    except Profile.DoesNotExist:
        return HttpResponseBadRequest("User doesn't have a profile!")

    if not utils.check_hmac_authentication(request,
                                           my_profile.account_secret):
        return HttpResponseForbidden()

    # Check any pending messages.  If these change status to "sent", we will
    # include them in the list of returned messages.

    messageHandler.check_pending_messages()

    # Construct a database query to retrieve the desired set of messages.

    if their_global_id != None:
        query = ((Q(sender_global_id=my_global_id) &
                  Q(recipient_global_id=their_global_id)) |
                 (Q(sender_global_id=their_global_id) &
                  Q(recipient_global_id=my_global_id)))
    else:
        query = (Q(sender_global_id=my_global_id) |
                 Q(recipient_global_id=my_global_id))

    # Perform the actual grabbing of the data with an exclusive table lock.
    # This prevents other clients from changing the data until we're finished.

    with dbHelpers.exclusive_access(Message):

        # Go through the list of messages we want to download, and mark any
        # messages sent to the current user as "read".  Note that this will
        # alter the update_id for these messages, so we have to do this before
        # we collect the final list of messages to return to the caller.

        messages_to_update = []
        for msg in Message.objects.filter(query):
            messages_to_update.append(msg)

        for msg in messages_to_update:
            if ((msg.recipient_global_id == my_global_id) and
                (msg.status == Message.STATUS_SENT)):
                msg.status = Message.STATUS_READ
                msg.save()

        # Collect the list of messages to return.

        messages = []
        for msg in Message.objects.filter(query).order_by("id"):
            timestamp = utils.datetime_to_unix_timestamp(msg.timestamp)
            status    = Message.STATUS_MAP[msg.status]

            messages.append({'hash'                 : msg.hash,
                             'timestamp'            : timestamp,
                             'sender_global_id'     : msg.sender_global_id,
                             'recipient_global_id'  : msg.recipient_global_id,
                             'sender_account_id'    : msg.sender_account_id,
                             'recipient_account_id' : msg.recipient_account_id,
                             'text'                 : msg.text,
                             'action'               : msg.action,
                             'action_params'        : msg.action_params,
                             'action_processed'     : msg.action_processed,
                             'amount_in_drops'      : msg.amount_in_drops,
                             'status'               : status})
            if msg.error:
                messages[-1]['error'] = msg.error

    # Finally, return the results back to the caller.

    return HttpResponse(json.dumps({'messages'    : messages}),
                        mimetype="application/json")

