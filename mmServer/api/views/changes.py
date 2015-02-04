""" mmServer.api.views.changes

    This module implements the "changes" endpoint for the mmServer.api
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
from mmServer.shared.lib    import utils, dbHelpers

#############################################################################

logger = logging.getLogger(__name__)

#############################################################################

@csrf_exempt
def endpoint(request):
    """ Respond to the "/api/changes" endpoint.

        This view function simply selects an appropriate handler based on the
        HTTP method.
    """
    try:
        if request.method == "GET":
            return changes_GET(request)
        else:
            return HttpResponseNotAllowed(["GET"])
    except:
        return utils.exception_response()

#############################################################################

def changes_GET(request):
    """ Respond to the "GET /api/changes" API request.

        This is used to poll for changes to our data.
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

    if "anchor" in request.GET:
        anchor = request.GET['anchor']
    else:
        anchor = None

    try:
        my_profile = Profile.objects.get(global_id=my_global_id)
    except Profile.DoesNotExist:
        return HttpResponseBadRequest("User doesn't have a profile")

    if not utils.check_hmac_authentication(request,
                                           my_profile.account_secret):
        return HttpResponseForbidden()

    # If we've been asked to return only the latest anchor value, do so.

    if anchor == None:
        with dbHelpers.exclusive_access(Profile, Picture, Conversation,
                                        Message):
            next_anchor = _calc_anchor()

        return HttpResponse(json.dumps({'next_anchor' : next_anchor}),
                            mimetype="application/json")

    # Parse the supplied anchor to get the various update IDs.

    anchor = _parse_anchor(anchor)
    if anchor == None:
        return HttpResponseBadRequest("Invalid anchor")

    # See if we have any pending messages.  If so, ask the Ripple network for
    # the current status of these messages, and finalize any that have either
    # failed or been accepted into the Ripple ledger.

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
            msg.save()

    # Look for any unread messages sent to the current user.  We mark these as
    # "read", since the user is about to receive notification about these
    # messages.

    query = Message.objects.filter(recipient_global_id=my_global_id)
    if "Message" in anchor:
        query = query.filter(update_id__gt=anchor['Message'])

    messages_to_update = []
    for msg in query:
        if msg.status == Message.STATUS_SENT:
            messages_to_update.append(msg)

    for msg in messages_to_update:
        msg.status = Message.STATUS_READ
        msg.save()

    # Get ready to start collecting updates.

    changes = []

    with dbHelpers.exclusive_access(Profile, Picture, Conversation, Message):

        # Get a list of all the global IDs that this user has conversed with.

        other_global_ids = []
        for c in Conversation.objects.filter(global_id_1=my_global_id):
            other_global_ids.append(c.global_id_2)
        for c in Conversation.objects.filter(global_id_2=my_global_id):
            other_global_ids.append(c.global_id_1)

        # Add any new or updated profiles for these users to the list of
        # changes.

        query = Profile.objects.filter(global_id__in=other_global_ids)
        if "Profile" in anchor:
            query = query.filter(update_id__gt=anchor['Profile'])

        for profile in query.order_by("update_id"):
            profile_data = {}
            profile_data['global_id'] = profile.global_id
            if profile.deleted:
                profile_data['deleted'] = True
            else:
                if profile.name_visible:
                    profile_data['name'] = profile.name
                if profile.location_visible:
                    profile_data['location'] = profile.location
                if profile.picture_visible:
                    profile_data['picture'] = profile.picture_id

            changes.append({'type' : "profile",
                            'data' : profile_data})

        # Add any new or updated pictures.

        query = Picture.objects.all()
        if "Picture" in anchor:
            query = query.filter(update_id__gt=anchor['Picture'])

        for picture in query.order_by("update_id"):
            picture_data = {}
            picture_data['picture_id'] = picture.picture_id
            if picture.deleted:
                picture_data['deleted'] = True
            picture_data['filename'] = picture.picture_filename

            changes.append({'type' : "picture",
                            'data' : picture_data})

        # Add any new or updated conversations involving this user.

        query = Conversation.objects.filter(Q(global_id_1=my_global_id) |
                                            Q(global_id_2=my_global_id))
        if "Conversation" in anchor:
            query = query.filter(update_id__gt=anchor['Conversation'])

        for conversation in query.order_by("update_id"):
            if conversation.last_timestamp != None:
                timestamp = utils.datetime_to_unix_timestamp(
                                                conversation.last_timestamp)
            else:
                timestamp = None

            data = {}
            data['my_global_id'] = my_global_id
            if conversation.global_id_1 == my_global_id:
                data['my_global_id']    = conversation.global_id_1
                data['their_global_id'] = conversation.global_id_2
                data['hidden']          = conversation.hidden_1
                data['num_unread']      = conversation.num_unread_1
            else:
                data['my_global_id']    = conversation.global_id_2
                data['their_global_id'] = conversation.global_id_1
                data['hidden']          = conversation.hidden_2
                data['num_unread']      = conversation.num_unread_2
            data['last_message']   = conversation.last_message
            data['last_timestamp'] = timestamp

            changes.append({'type' : "conversation",
                            'data' : data})

        # Add any new or updated messages involving this user.

        query = Message.objects.filter(Q(sender_global_id=my_global_id) |
                                       Q(recipient_global_id=my_global_id))
        if "Message" in anchor:
            query = query.filter(update_id__gt=anchor['Message'])

        for message in query.order_by("update_id"):
            timestamp = utils.datetime_to_unix_timestamp(message.timestamp)
            status    = Message.STATUS_MAP[message.status]

            msg_data = {}
            msg_data['hash']                = message.hash
            msg_data['timestamp']           = timestamp
            msg_data['sender_global_id']    = message.sender_global_id
            msg_data['recipient_global_id'] = message.recipient_global_id
            msg_data['sender_account_id']   = message.sender_account_id
            msg_data['recipient_account_id'] = message.recipient_account_id
            msg_data['text']                = message.text
            msg_data['action']              = message.action
            msg_data['action_params']       = message.action_params
            msg_data['action_processed']    = message.action_processed
            msg_data['amount_in_drops']     = message.amount_in_drops
            msg_data['status']              = Message.STATUS_MAP[message.status]

            if message.error != None:
                msg_data['error'] = message.error

            changes.append({'type' : "message",
                            'data' : msg_data})

        # Finally, calculate the updated anchor value for this state of the
        # system.

        next_anchor = _calc_anchor()

    # Return the accumulated results back to the caller.

    return HttpResponse(json.dumps({'changes'     : changes,
                                    'next_anchor' : next_anchor}),
                        mimetype="application/json")

#############################################################################
##                                                                         ##
##                   P R I V A T E   D E F I N I T I O N S                 ##
##                                                                         ##
#############################################################################

def _calc_anchor():
    """ Calculate and return the current anchor value.

        Note that this function assumes that we have exclusive database access
        to the Profile, Picture, Conversation and Message tables.
    """
    anchor = {} # Maps model name to current update ID.

    max_value = Profile.objects.all().aggregate(Max('update_id'))
    if max_value['update_id__max'] != None:
        anchor['Profile'] = max_value['update_id__max']

    max_value = Picture.objects.all().aggregate(Max('update_id'))
    if max_value['update_id__max'] != None:
        anchor['Picture'] = max_value['update_id__max']

    max_value = Conversation.objects.all().aggregate(Max('update_id'))
    if max_value['update_id__max'] != None:
        anchor['Conversation'] = max_value['update_id__max']

    max_value = Message.objects.all().aggregate(Max('update_id'))
    if max_value['update_id__max'] != None:
        anchor['Message'] = max_value['update_id__max']

    return base64.urlsafe_b64encode(json.dumps(anchor))

#############################################################################

def _parse_anchor(anchor):
    """ Extract the various update IDs from the given anchor value.

        We return a dictionary mapping model names to update IDs.

        If the anchor can't be parsed, we return None.
    """
    try:
        anchor = base64.urlsafe_b64decode(str(anchor))
    except TypeError:
        return None

    try:
        anchor = json.loads(anchor)
    except json.JSONDecodeError:
        return None

    return anchor

