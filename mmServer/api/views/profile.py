""" mmServer.api.views.profile

    This module implements the "profile" endpoint for the mmServer.api
    application.
"""
import logging

from django.http                  import *
from django.views.decorators.csrf import csrf_exempt

import simplejson as json

from mmServer.shared.models import *
from mmServer.shared.lib    import utils

#############################################################################

logger = logging.getLogger(__name__)

#############################################################################

@csrf_exempt
def endpoint(request, global_id):
    """ Respond to the "/api/profile/<GLOBAL_ID>" endpoint.

        This view function simply selects an appropriate handler based on the
        HTTP method.
    """
    if request.method == "GET":
        return profile_GET(request, global_id)
    elif request.method == "POST":
        return profile_POST(request, global_id)
    elif request.method == "PUT":
        return profile_PUT(request, global_id)
    elif request.method == "DELETE":
        return profile_DELETE(request, global_id)
    else:
        return HttpResponseNotAllowed(["GET", "POST", "PUT", "DELETE"])

#############################################################################

def profile_GET(request, global_id):
    """ Respond to the "GET /api/profile/<GLOBAL_ID>" API request.

        This is used to retrieve a user's profile.
    """
    if utils.has_hmac_headers(request):
        # The caller is attempting to make an authenticated request to retrieve
        # the user's entire profile.

        try:
            profile = Profile.objects.get(global_id=global_id)
        except Profile.DoesNotExist:
            return HttpResponseNotFound()

        if not utils.check_hmac_authentication(request,
                                               profile.account_secret):
            return HttpResponseForbidden()

        # If we get here, the caller is authenticated -> return the full
        # profile details.

        response = {'global_id'        : profile.global_id,
                    'name'             : profile.name,
                    'name_visible'     : profile.name_visible,
                    'location'         : profile.location,
                    'location_visible' : profile.location_visible,
                    'picture_id'       : profile.picture_id,
                    'picture_visible'  : profile.picture_visible}

        return HttpResponse(json.dumps(response),
                            mimetype="application/json")
    else:
        # The caller is making an unauthenticated request.  We simply return
        # the public details for the given profile.

        try:
            profile = Profile.objects.get(global_id=global_id)
        except Profile.DoesNotExist:
            return HttpResponseNotFound()

        response = {'global_id' : profile.global_id}
        if profile.name_visible:
            response['name'] = profile.name
        if profile.location_visible:
            response['location'] = profile.location
        if profile.picture_visible:
            response['picture_id'] = profile.picture_id

        return HttpResponse(json.dumps(response),
                            mimetype="application/json")

#############################################################################

def profile_POST(request, global_id):
    """ Respond to the "POST /api/profile/<GLOBAL_ID>" API request.

        This is used to create a user profile.
    """
    if not utils.has_hmac_headers(request):
        return HttpResponseForbidden()

    try:
        existing_profile = Profile.objects.get(global_id=global_id)
    except Profile.DoesNotExist:
        existing_profile = None

    if existing_profile != None:
        return HttpResponse("DUPLICATE", status=409)

    if request.META['CONTENT_TYPE'] != "application/json":
        return HttpResponseBadRequest()

    data = json.loads(request.body)
    if "account_secret" not in data:
        return HttpResponseBadRequest()
    else:
        account_secret = data['account_secret']

    if "profile" not in data:
        return HttpResponseBadRequest()
    else:
        profile_data = data['profile']

    if not utils.check_hmac_authentication(request, account_secret):
        return HttpResponseForbidden()

    profile = Profile()
    profile.global_id        = global_id
    profile.account_secret   = account_secret
    profile.name             = profile_data.get("name" "")
    profile.name_visible     = profile_data.get("name_visible", False)
    profile.location         = profile_data.get("location", "")
    profile.location_visible = profile_data.get("location_visible", False)
    profile.picture_id       = profile_data.get("picture_id", "")
    profile.picture_visible  = profile_data.get("picture_visible", False)

    profile.save()

    return HttpResponse(status=201)

#############################################################################

def profile_PUT(request, global_id):
    """ Respond to the "PUT /api/profile/<GLOBAL_ID>" API request.

        This is used to update a user's profile.
    """
    if not utils.has_hmac_headers(request):
        return HttpResponseForbidden()

    try:
        profile = Profile.objects.get(global_id=global_id)
    except Profile.DoesNotExist:
        return HttpResponseNotFound()

    if not utils.check_hmac_authentication(request, profile.account_secret):
        return HttpResponseForbidden()

    if request.META['CONTENT_TYPE'] != "application/json":
        return HttpResponseBadRequest()

    changes = json.loads(request.body)

    if "name" in changes:
        profile.name = changes['name']
    if "name_visible" in changes:
        profile.name_visible = changes['name_visible']
    if "location" in changes:
        profile.location = changes['location']
    if "location_visible" in changes:
        profile.location_visible = changes['location_visible']
    if "picture_id" in changes:
        profile.picture_id = changes['picture_id']
    if "picture_visible" in changes:
        profile.picture_visible = changes['picture_visible']

    profile.save()

    return HttpResponse(status=200)

#############################################################################

def profile_DELETE(request, global_id):
    """ Respond to the "DELETE /api/profile/<GLOBAL_ID>" API request.

        This is used to delete a user's profile.
    """
    if not utils.has_hmac_headers(request):
        return HttpResponseForbidden()

    try:
        profile = Profile.objects.get(global_id=global_id)
    except Profile.DoesNotExist:
        return HttpResponseNotFound()

    if not utils.check_hmac_authentication(request, profile.account_secret):
        return HttpResponseForbidden()

    profile.delete()

    return HttpResponse(status=200)

