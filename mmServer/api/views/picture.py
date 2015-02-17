""" mmServer.api.views.picture

    This module implements the "picture" endpoint for the mmServer.api
    application.
"""
import base64
import cStringIO
import logging
import io
import math
import os.path
import uuid

from django.http                  import *
from django.views.decorators.csrf import csrf_exempt

import simplejson as json

from PIL import Image

from mmServer.shared.models import *
from mmServer.shared.lib    import utils

#############################################################################

logger = logging.getLogger(__name__)

#############################################################################

@csrf_exempt
def endpoint(request, picture_id=None):
    """ Respond to the "/api/picture[/<GLOBAL_ID>]" endpoint.

        This view function simply selects an appropriate handler based on the
        HTTP method.
    """
    try:
        if request.method == "GET":
            return picture_GET(request, picture_id)
        elif request.method == "POST":
            if picture_id != None:
                return HttpResponseNotFound()
            else:
                return picture_POST(request)
        elif request.method == "PUT":
            return picture_PUT(request, picture_id)
        elif request.method == "DELETE":
            return picture_DELETE(request, picture_id)
        else:
            return HttpResponseNotAllowed(["GET", "POST", "PUT", "DELETE"])
    except:
        return utils.exception_response()

#############################################################################

def picture_GET(request, picture_id):
    """ Respond to the "GET /api/picture/<PICTURE_ID>" API request.

        This is used to retrieve an uploaded picture.
    """
    if "max_width" in request.GET:
        try:
            max_width = int(request.GET['max_width'])
        except ValueError:
            return HttpResponseBadRequest()
    else:
        max_width = None

    if "max_height" in request.GET:
        try:
            max_height = int(request.GET['max_height'])
        except ValueError:
            return HttpResponseBadRequest()
    else:
        max_height = None

    try:
        picture = Picture.objects.get(picture_id=picture_id)
    except Picture.DoesNotExist:
        return HttpResponseNotFound()

    basename,extension = os.path.splitext(picture.picture_filename)
    extension = extension.lower()
    if extension.startswith("."):
        imageType = extension[1:]

    try:
        image_data = base64.b64decode(picture.picture_data)
    except TypeError:
        return HttpResponseBadRequest() # ???

    if (max_width != None) or (max_height != None):
        # Scale the image to fit within the given maximum dimension(s).
        image = Image.open(io.BytesIO(image_data))
        width,height = image.size

        if max_width != None and max_height != None:
            if width > height:
                if max_width != None and width > max_width:
                    scale_factor = float(max_width) / float(width)
                    height       = int(math.ceil(height * scale_factor))
                    width        = max_width
            else:
                if max_height != None and height > max_height:
                    scale_factor = float(max_height) / float(height)
                    width        = int(math.ceil(width * scale_factor))
                    height       = max_height
        elif max_width != None:
            if width > max_width:
                scale_factor = float(max_width) / float(width)
                height       = int(math.ceil(height * scale_factor))
                width        = max_width
        elif max_height != None:
            if height > max_height:
                scale_factor = float(max_height) / float(height)
                width        = int(math.ceil(width * scale_factor))
                height       = max_height

        scaled_image = image.resize((width, height), Image.LANCZOS)

        buffer = cStringIO.StringIO()
        scaled_image.save(buffer, format=imageType)
        image_data = buffer.getvalue()
        buffer.close()

    return HttpResponse(image_data,
                        mimetype="image/" + imageType)

#############################################################################

def picture_POST(request):
    """ Respond to the "POST /api/picture" API request.

        This is used to upload a new picture.
    """
    if not utils.has_hmac_headers(request):
        return HttpResponseForbidden()

    if request.META['CONTENT_TYPE'] != "application/json":
        return HttpResponseBadRequest("Request must be in JSON format.")

    data = json.loads(request.body)

    if "account_secret" not in data:
        return HttpResponseBadRequest("Missing 'account_secret' field.")
    else:
        account_secret = data['account_secret']

    if "picture_filename" not in data:
        return HttpResponseBadRequest("Missing 'picture_filename' field.")
    else:
        picture_filename = data['picture_filename']

    if "picture_data" not in data:
        return HttpResponseBadRequest("Missing 'picture_data' field.")
    else:
        picture_data = data['picture_data']

    try:
        raw_data = base64.b64decode(picture_data)
    except TypeError:
        return HttpResponseBadRequest("Picture data not in base64 encoding.")

    if not utils.check_hmac_authentication(request, account_secret):
        return HttpResponseForbidden()

    picture_id = uuid.uuid4().hex

    picture = Picture()
    picture.picture_id = picture_id
    picture.account_secret = account_secret
    picture.picture_filename = picture_filename
    picture.picture_data     = picture_data
    picture.save()

    return HttpResponse(picture_id, status=201)

#############################################################################

def picture_PUT(request, picture_id):
    """ Respond to the "PUT /api/picture/<picture_ID>" API request.

        This is used to update a picture.
    """
    if not utils.has_hmac_headers(request):
        return HttpResponseForbidden()

    try:
        picture = Picture.objects.get(picture_id=picture_id)
    except Picture.DoesNotExist:
        return HttpResponseNotFound()

    if not utils.check_hmac_authentication(request, picture.account_secret):
        return HttpResponseForbidden()

    if request.META['CONTENT_TYPE'] != "application/json":
        return HttpResponseBadRequest("Request must be in JSON format.")

    data = json.loads(request.body)

    if "picture_filename" not in data:
        return HttpResponseBadRequest("Missing 'picture_filename' field.")
    else:
        picture_filename = data['picture_filename']

    if "picture_data" not in data:
        return HttpResponseBadRequest("Missing 'picture_data' field.")
    else:
        picture_data = data['picture_data']

    try:
        raw_data = base64.b64decode(picture_data)
    except TypeError:
        return HttpResponseBadRequest("Picture data not in base64 encoding.")

    picture.picture_filename = picture_filename
    picture.picture_data     = picture_data
    picture.save()

    return HttpResponse(status=200)

#############################################################################

def picture_DELETE(request, picture_id):
    """ Respond to the "DELETE /api/picture/<PICTURE_ID>" API request.

        This is used to delete a picture.
    """
    if not utils.has_hmac_headers(request):
        return HttpResponseForbidden()

    try:
        picture = Picture.objects.get(picture_id=picture_id)
    except Picture.DoesNotExist:
        return HttpResponseNotFound()

    if not utils.check_hmac_authentication(request, picture.account_secret):
        return HttpResponseForbidden()

    picture.deleted = True
    picture.save()

    return HttpResponse(status=200)

