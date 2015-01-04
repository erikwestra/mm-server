""" mmServer.api.views.conversation

    This module implements the "conversation" endpoint for the mmServer.api
    application.
"""
import logging

from django.http                  import *
from django.views.decorators.csrf import csrf_exempt
from django.utils                 import timezone

import simplejson as json

from mmServer.shared.models import *
from mmServer.shared.lib    import utils

#############################################################################

logger = logging.getLogger(__name__)

#############################################################################

@csrf_exempt
def endpoint(request):
    """ Respond to the "/api/conversation" endpoint.

        This view function simply selects an appropriate handler based on the
        HTTP method.
    """
    if request.method == "GET":
        return conversation_GET(request)
    elif request.method == "POST":
        return conversation_POST(request)
    elif request.method == "PUT":
        return conversation_PUT(request)
    else:
        return HttpResponseNotAllowed(["GET", "POST", "PUT"])

#############################################################################

def conversation_GET(request):
    """ Respond to the "GET /api/conversation" API request.

        This is used to retrieve a single conversation.
    """
    # Process our parameters, and check the HMAC authentication.

    if not utils.has_hmac_headers(request):
        return HttpResponseForbidden()

    if "my_global_id" not in request.GET:
        return HttpResponseBadRequest("Missing 'my_global_id' parameter")
    else:
        my_global_id = request.GET['my_global_id']

    if "their_global_id" not in request.GET:
        return HttpResponseBadRequest("Missing 'their_global_id' parameter")
    else:
        their_global_id = request.GET['their_global_id']

    try:
        my_profile = Profile.objects.get(global_id=my_global_id)
    except Profile.DoesNotExist:
        return HttpResponseForbidden()

    if not utils.check_hmac_authentication(request, my_profile.account_secret):
        return HttpResponseForbidden()

    # Get the requested conversation, if it exists.

    try:
        conversation = Conversation.objects.get(global_id_1=my_global_id,
                                                global_id_2=their_global_id)
    except Conversation.DoesNotExist:
        try:
            conversation = Conversation.objects.get(global_id_1=their_global_id,
                                                    global_id_2=my_global_id)
        except:
            return HttpResponseNotFound()

    # Adapt the conversation to this user's point of view.

    if conversation.last_timestamp != None:
        timestamp = utils.datetime_to_unix_timestamp(
                                        conversation.last_timestamp)
    else:
        timestamp = None

    if my_global_id == conversation.global_id_1:
        adapted = {'my_global_id'    : conversation.global_id_1,
                   'their_global_id' : conversation.global_id_2,
                   'hidden'          : conversation.hidden_1,
                   'last_message'    : conversation.last_message,
                   'last_timestamp'  : timestamp,
                   'num_unread'      : conversation.num_unread_1}
    else:
        adapted = {'my_global_id'    : conversation.global_id_2,
                   'their_global_id' : conversation.global_id_1,
                   'hidden'          : conversation.hidden_2,
                   'last_message'    : conversation.last_message,
                   'last_timestamp'  : timestamp,
                   'num_unread'      : conversation.num_unread_2}

    # Return the results back to the caller.

    return HttpResponse(json.dumps({'conversation' : adapted}),
                        mimetype="application/json")

#############################################################################

def conversation_POST(request):
    """ Respond to the "POST /api/conversation" API request.

        This is used to create a conversation.
    """
    # Process our parameters, and check the HMAC authentication.

    if not utils.has_hmac_headers(request):
        return HttpResponseForbidden()

    if request.META['CONTENT_TYPE'] != "application/json":
        return HttpResponseBadRequest()

    data = json.loads(request.body)

    if "my_global_id" not in data:
        return HttpResponseBadRequest()
    else:
        my_global_id = data['my_global_id']

    if "their_global_id" not in data:
        return HttpResponseBadRequest()
    else:
        their_global_id = data['their_global_id']

    try:
        my_profile = Profile.objects.get(global_id=my_global_id)
    except Profile.DoesNotExist:
        return HttpResponseForbidden()

    if not utils.check_hmac_authentication(request, my_profile.account_secret):
        return HttpResponseForbidden()

    # See if we already have a conversation between these two users.

    try:
        existing = Conversation.objects.get(global_id_1=my_global_id,
                                            global_id_2=their_global_id)
    except Conversation.DoesNotExist:
        try:
            existing = Conversation.objects.get(global_id_1=their_global_id,
                                                global_id_2=my_global_id)
        except:
            existing = None

    if existing != None:
        return HttpResponse("DUPLICATE", status=409)

    # Create the new conversation.

    conversation = Conversation()
    conversation.global_id_1    = my_global_id
    conversation.global_id_2    = their_global_id
    conversation.hidden_1       = False
    conversation.hidden_2       = False
    conversation.last_message   = None
    conversation.last_timestamp = None
    conversation.num_unread_1   = 0
    conversation.num_unread_2   = 0
    conversation.save()

    # All done.  Tell the caller the good news.

    return HttpResponse(status=201)

#############################################################################

def conversation_PUT(request):
    """ Respond to the "PUT /api/conversation" API request.

        This is used to update a conversation.
    """
    # Process our parameters, and check the HMAC authentication.

    if not utils.has_hmac_headers(request):
        return HttpResponseForbidden()

    if request.META['CONTENT_TYPE'] != "application/json":
        return HttpResponseBadRequest()

    data = json.loads(request.body)

    if "my_global_id" not in data:
        return HttpResponseBadRequest()
    else:
        my_global_id = data['my_global_id']

    if "their_global_id" not in data:
        return HttpResponseBadRequest()
    else:
        their_global_id = data['their_global_id']

    if "action" not in data:
        return HttpResponseBadRequest()
    else:
        action = data['action']

    if "message" in data:
        message = data['message']
    else:
        message = None

    if action not in ["NEW_MESSAGE", "READ", "HIDE", "UNHIDE"]:
        return HttpResponseBadRequest()

    try:
        my_profile = Profile.objects.get(global_id=my_global_id)
    except Profile.DoesNotExist:
        return HttpResponseForbidden()

    if not utils.check_hmac_authentication(request, my_profile.account_secret):
        return HttpResponseForbidden()

    # Get the requested conversation, if it exists.

    try:
        conversation = Conversation.objects.get(global_id_1=my_global_id,
                                                global_id_2=their_global_id)
    except Conversation.DoesNotExist:
        try:
            conversation = Conversation.objects.get(global_id_1=their_global_id,
                                                    global_id_2=my_global_id)
        except:
            return HttpResponseNotFound()

    # Update the conversation as appropriate.

    if action == "NEW_MESSAGE":

        if message == None:
            return HttpResponseBadRequest()

        conversation.last_message   = message
        conversation.last_timestamp = timezone.now()

        if conversation.global_id_1 == my_global_id:
            conversation.num_unread_2 = conversation.num_unread_2 + 1
        else:
            conversation.num_unread_1 = conversation.num_unread_1 + 1

    elif action == "READ":

        if conversation.global_id_1 == my_global_id:
            conversation.num_unread_1 = 0
        else:
            conversation.num_unread_2 = 0

    elif action == "HIDE":

        if conversation.global_id_1 == my_global_id:
            conversation.hidden_1 = True
        else:
            conversation.hidden_2 = True

    elif action == "UNHIDE":

        if conversation.global_id_1 == my_global_id:
            conversation.hidden_1 = False
        else:
            conversation.hidden_2 = False

    conversation.save()

    # Finally, tell the caller the good news.

    return HttpResponse(status=200)

