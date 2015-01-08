""" mmServer.api.views.conversations

    This module implements the "conversations" endpoint for the mmServer.api
    application.
"""
import datetime
import logging
import operator

from django.http                  import *
from django.core.paginator        import *
from django.views.decorators.csrf import csrf_exempt
from django.utils                 import timezone

import simplejson as json

from mmServer.shared.models import *
from mmServer.shared.lib    import utils

#############################################################################

logger = logging.getLogger(__name__)

#############################################################################

@csrf_exempt
def endpoint(request, global_id):
    """ Respond to the "/api/conversations/<GLOBAL-ID>" endpoint.

        This view function simply selects an appropriate handler based on the
        HTTP method.
    """
    if request.method == "GET":
        return conversations_GET(request, global_id)
    else:
        return HttpResponseNotAllowed(["GET"])

#############################################################################

def conversations_GET(request, global_id):
    """ Respond to the "GET /api/conversations/<GLOBAL-ID" API request.

        This is used to retrieve a user's conversations.
    """
    if not utils.has_hmac_headers(request):
        return HttpResponseForbidden()

    try:
        profile = Profile.objects.get(global_id=global_id)
    except Profile.DoesNotExist:
        return HttpResponseNotFound()

    if not utils.check_hmac_authentication(request, profile.account_secret):
        return HttpResponseForbidden()

    conversations = [] # List of matching conversations.

    for conversation in Conversation.objects.filter(global_id_1=global_id):
        if conversation.last_timestamp != None:
            timestamp = utils.datetime_to_unix_timestamp(
                                                conversation.last_timestamp)
        else:
            timestamp = None

        conversations.append({'my_global_id'    : conversation.global_id_1,
                              'their_global_id' : conversation.global_id_2,
                              'encryption_key'  : conversation.encryption_key,
                              'hidden'          : conversation.hidden_1,
                              'last_message'    : conversation.last_message,
                              'last_timestamp'  : timestamp,
                              'num_unread'      : conversation.num_unread_1})

    for conversation in Conversation.objects.filter(global_id_2=global_id):
        if conversation.last_timestamp != None:
            timestamp = utils.datetime_to_unix_timestamp(
                                                conversation.last_timestamp)
        else:
            timestamp = None

        conversations.append({'my_global_id'    : conversation.global_id_2,
                              'their_global_id' : conversation.global_id_1,
                              'encryption_key'  : conversation.encryption_key,
                              'hidden'          : conversation.hidden_2,
                              'last_message'    : conversation.last_message,
                              'last_timestamp'  : timestamp,
                              'num_unread'      : conversation.num_unread_2})

    conversations.sort(key=operator.itemgetter("last_timestamp"), reverse=True)

    return HttpResponse(json.dumps({'conversations' : conversations}),
                        mimetype="application/json")

