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
    try:
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
    except:
        return utils.exception_response()

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

        if profile.deleted:
            response = {'global_id' : profile.global_id,
                        'deleted'   : True}
        else:
            response = {'global_id'          : profile.global_id,
                        'name'               : profile.name,
                        'name_visible'       : profile.name_visible,
                        'email'              : profile.email,
                        'phone'              : profile.phone,
                        'address_1'          : profile.address_1,
                        'address_1_visible'  : profile.address_1_visible,
                        'address_2'          : profile.address_2,
                        'address_2_visible'  : profile.address_2_visible,
                        'city'               : profile.city,
                        'city_visible'       : profile.city_visible,
                        'state_province_or_region' :
                            profile.state_province_or_region,
                        'state_province_or_region_visible' :
                            profile.state_province_or_region_visible,
                        'zip_or_postal_code' : profile.zip_or_postal_code,
                        'zip_or_postal_code_visible' :
                            profile.zip_or_postal_code_visible,
                        'country'            : profile.country,
                        'country_visible'    : profile.country_visible,
                        'date_of_birth'      :
                            utils.date_to_string(profile.date_of_birth),
                        'social_security_number_last_4_digits' :
                            profile.social_security_number_last_4_digits,
                        'bio'                : profile.bio,
                        'bio_visible'        : profile.bio_visible,
                        'picture_id'         : profile.picture_id,
                        'picture_id_visible' : profile.picture_id_visible}

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
        if profile.deleted:
            response['deleted'] = True
        else:
            if profile.name_visible:
                response['name'] = profile.name
            if profile.address_1_visible:
                response['address_1'] = profile.address_1
            if profile.address_2_visible:
                response['address_2'] = profile.address_2
            if profile.city_visible:
                response['city'] = profile.city
            if profile.state_province_or_region_visible:
                response['state_province_or_region'] = \
                    profile.state_province_or_region
            if profile.zip_or_postal_code_visible:
                response['zip_or_postal_code'] = profile.zip_or_postal_code
            if profile.country_visible:
                response['country'] = profile.country
            if profile.bio_visible:
                response['bio'] = profile.bio
            if profile.picture_id_visible:
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

    if "date_of_birth" in profile_data:
        date_of_birth = utils.string_to_date(profile_data['date_of_birth'])
        if date_of_birth == None:
            return HttpResponseBadRequest("Invalid date_of_birth value.")
    else:
        date_of_birth = None

    profile = Profile()
    profile.global_id           = global_id
    profile.account_secret      = account_secret
    profile.name                = profile_data.get("name" "")
    profile.name_visible        = profile_data.get("name_visible", False)
    profile.email               = profile_data.get("email", "")
    profile.phone               = profile_data.get("phone", "")
    profile.address_1           = profile_data.get("address_1", "")
    profile.address_1_visible   = profile_data.get("address_1_visible", False)
    profile.address_2           = profile_data.get("address_2", "")
    profile.address_2_visible   = profile_data.get("address_2_visible", False)
    profile.city                = profile_data.get("city", "")
    profile.city_visible        = profile_data.get("city_visible", False)
    profile.state_province_or_region = profile_data.get(
                                            "state_province_or_region", "")
    profile.state_province_or_region_visible = profile_data.get(
                                    "state_province_or_region_visible", False)
    profile.zip_or_postal_code  = profile_data.get("zip_or_postal_code", "")
    profile.zip_or_postal_code_visible = profile_data.get(
                                    "zip_or_postal_code_visible", False)
    profile.country             = profile_data.get("country", "")
    profile.country_visible     = profile_data.get("country_visible", False)
    profile.date_of_birth       = date_of_birth
    profile.social_security_number_last_4_digits = \
        profile_data.get("social_security_number_last_4_digits", "")
    profile.bio                 = profile_data.get("bio", "")
    profile.bio_visible         = profile_data.get("bio_visible", False)
    profile.picture_id          = profile_data.get("picture_id", "")
    profile.picture_id_visible  = profile_data.get("picture_id_visible", False)

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
    if "email" in changes:
        profile.email = changes['email']
    if "phone" in changes:
        profile.phone = changes['phone']
    if "address_1" in changes:
        profile.address_1 = changes['address_1']
    if "address_1_visible" in changes:
        profile.address_1_visible = changes['address_1_visible']
    if "address_2" in changes:
        profile.address_2 = changes['address_2']
    if "address_2_visible" in changes:
        profile.address_2_visible = changes['address_2_visible']
    if "city" in changes:
        profile.city = changes['city']
    if "city_visible" in changes:
        profile.city_visible = changes['city_visible']
    if "state_province_or_region" in changes:
        profile.state_province_or_region = changes['state_province_or_region']
    if "state_province_or_region_visible" in changes:
        profile.state_province_or_region_visible = \
            changes['state_province_or_region_visible']
    if "zip_or_postal_code" in changes:
        profile.zip_or_postal_code = changes['zip_or_postal_code']
    if "zip_or_postal_code_visible" in changes:
        profile.zip_or_postal_code_visible = \
            changes['zip_or_postal_code_visible']
    if "country" in changes:
        profile.country = changes['country']
    if "country_visible" in changes:
        profile.country_visible = changes['country_visible']
    if "date_of_birth" in changes:
        date_of_birth = utils.string_to_date(changes['date_of_birth'])
        if date_of_birth == None:
            return HttpResponseBadRequest("Invalid date_of_birth value")
        else:
            profile.date_of_birth = date_of_birth
    if "social_security_number_last_4_digits" in changes:
        profile.social_security_number_last_4_digits = \
            changes['social_security_number_last_4_digits']
    if "bio" in changes:
        profile.bio = changes['bio']
    if "bio_visible" in changes:
        profile.bio_visible = changes['bio_visible']
    if "picture_id" in changes:
        profile.picture_id = changes['picture_id']
    if "picture_id_visible" in changes:
        profile.picture_id_visible = changes['picture_id_visible']

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

    profile.deleted = True
    profile.save()

    return HttpResponse(status=200)

