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

    if "num_msgs" in request.GET:
        try:
            num_msgs = int(request.GET['num_msgs'])
        except ValueError:
            return HttpResponseBadRequest("Invalid 'num_msgs' parameter.")
    else:
        num_msgs = 20

    if "from_msg" in request.GET:
        from_msg = request.GET['from_msg']
    else:
        from_msg = None

    # Check the caller's authentication.

    try:
        my_profile = Profile.objects.get(global_id=my_global_id)
    except Profile.DoesNotExist:
        return HttpResponseBadRequest("User doesn't have a profile")

    if not utils.check_hmac_authentication(request,
                                           my_profile.account_secret):
        return HttpResponseForbidden()

    # Check any pending messages.  If these change status to "sent", we will
    # include them in the list of returned messages.

    messageHandler.check_pending_messages()

    # Perform the actual grabbing of the data with an exclusive table lock.
    # This prevents other clients from changing the data until we're finished.

    with dbHelpers.exclusive_access(Message):

        # Construct a database query to retrieve the desired set of messages.
        # Note that we process the messages in reverse, starting with the most
        # recent matching message.

        if their_global_id != None:
            filter = ((Q(sender_global_id=my_global_id) &
                       Q(recipient_global_id=their_global_id)) |
                      (Q(sender_global_id=their_global_id) &
                       Q(recipient_global_id=my_global_id)))
        else:
            filter = (Q(sender_global_id=my_global_id) |
                      Q(recipient_global_id=my_global_id))

        query = Message.objects.filter(filter).order_by("-id")
        if from_msg != None:
            try:
                msg = Message.objects.get(hash=from_msg)
            except msg.DoesNotExist:
                msg = None

            if msg == None:
                return HttpResponseBadRequest("'from_msg' not a message hash")

            query = query.filter(id__lt=msg.id)

        if num_msgs != -1:
            query = query[:num_msgs+1]

        # Collect the list of messages to return.

        messages = []
        has_more = False # initially.

        for msg in query:
            if num_msgs != -1 and len(messages) == num_msgs:
                # We've got at least one more message than was asked for.
                has_more = True
                continue

            timestamp = utils.datetime_to_unix_timestamp(msg.timestamp)
            status    = Message.STATUS_MAP[msg.status]

            message = {'hash'                 : msg.hash,
                       'timestamp'            : timestamp,
                       'sender_global_id'     : msg.sender_global_id,
                       'recipient_global_id'  : msg.recipient_global_id,
                       'sender_account_id'    : msg.sender_account_id,
                       'recipient_account_id' : msg.recipient_account_id,
                       'sender_text'          : msg.sender_text,
                       'recipient_text'       : msg.recipient_text,
                       'action'               : msg.action,
                       'action_params'        : msg.action_params,
                       'action_processed'     : msg.action_processed,
                       'system_charge'        : msg.system_charge,
                       'recipient_charge'     : msg.recipient_charge,
                       'status'               : status}
            if msg.error:
                message['error'] = msg.error

            messages.append(message)

        messages.reverse() # Return the newest message last, not first.

    # Finally, return the results back to the caller.

    return HttpResponse(json.dumps({'messages' : messages,
                                    'has_more' : has_more}),
                        mimetype="application/json")

