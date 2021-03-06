""" mmServer.shared.lib.utils

    This module define various utility functions used by the mmServer system.
"""
import base64
import datetime
import hashlib
import logging
import random
import string
import sys
import traceback
import uuid

from django.utils     import timezone
from django.http      import HttpResponseServerError

from mmServer.shared.models import *

#############################################################################

logger = logging.getLogger("mmServer")

#############################################################################

def random_string(min_length=5, max_length=10):
    """ Generate and return a string of random lowercase letters and digits.

        The returned string will consist only of lowercase letters and digits,
        and be between the given minimum and maximum length.
    """
    length = random.randint(min_length, max_length)
    chars = []
    for i in range(length):
        chars.append(random.choice(string.lowercase+string.digits))
    return "".join(chars)

#############################################################################

def calc_unique_global_id():
    """ Create and return a new random global_id value.
    """
    while True:
        global_id = random_string()
        try:
            existing_profile = Profile.objects.get(global_id=global_id)
        except Profile.DoesNotExist:
            existing_profile = None

        if existing_profile == None:
            break
        else:
            continue # Keep trying until we get a unique global_id.

    return global_id

#############################################################################

def calc_unique_picture_id():
    """ create and return a new random picture_id value.
    """
    while True:
        picture_id = random_string()
        try:
            existing_picture = Picture.objects.get(picture_id=picture_id)
        except Picture.DoesNotExist:
            existing_picture = None

        if existing_picture == None:
            break
        else:
            continue # Keep trying until we get a unique global_id.

    return picture_id

#############################################################################

def calc_hmac_headers(method, url, body, account_secret):
    """ Return the HTTP headers to use for an HMAC-authenticated request.

        The parameters are as follows:

            'method'

                The HTTP method to use for this request.

            'url'

                The full URL for the desired endpoint, excluding the server
                name.

            'body'

                The body of the HTTP request, as a string.

            'account_secret'

                The account secret for the user we are making an authenticated
                request for.

        We calculate the HMAC authentication headers to use for making an
        authenticated request to the server.  The headers are returned in the
        form of a dictionary mapping header fields to values.
    """
    nonce       = uuid.uuid4().hex
    content_md5 = hashlib.md5(body).hexdigest()
    parts       = [method, url, content_md5, nonce, account_secret]
    hmac_digest = hashlib.sha1("\n".join(parts)).hexdigest()
    hmac_base64 = base64.b64encode(hmac_digest)

    return {'Authorization' : "HMAC " + hmac_base64,
            'Content_MD5'   : content_md5,
            'Nonce'         : nonce}

#############################################################################

def normalize_request_headers(request):
    """ Normalize the request headers for the given HTTP request.

        The HTTP headers for the given request (in request.META) are converted
        to uppercase, and have the string "HTTP_" removed from the start.  This
        avoids problems with different headers while unit testing versus
        running the live system.

        Upon completion, we return a dictionary mapping normalized request
        headers to their associated values.
    """
    headers = {}
    for header in request.META.keys():
        normalized_header = header.upper()
        if normalized_header.startswith("HTTP_"):
            normalized_header = normalized_header[5:]
        headers[normalized_header] = request.META[header]
    return headers

#############################################################################

def has_hmac_headers(request):
    """ Return True if the given request includes HMAC-authentication headers.
    """
    headers = normalize_request_headers(request)
    if "AUTHORIZATION" not in headers: return False
    if "CONTENT_MD5"   not in headers: return False
    if "NONCE"         not in headers: return False
    return True

#############################################################################

def check_hmac_authentication(request, account_secret):
    """ Return True if the given request's HMAC-authentication is correct.

        The parameters are as follows:

            'request'

                An HttpRequest object for the current request.  This will
                include the HMAC-authentication headers.

            'account_secret'

                The account secret that should have been used to calculate the
                HMAC authentication headers.

        If the given request's HMAC-authentication headers are correct for the
        given account secret, we return True.
    """
    headers = normalize_request_headers(request)

    NonceValue.objects.purge()

    http_method      = request.method
    url              = request.path

    hmac_auth_string = headers.get("AUTHORIZATION")
    content_md5      = headers.get("CONTENT_MD5")
    nonce            = headers.get("NONCE")

    if hmac_auth_string == None or content_md5 == None or nonce == None:
        logger.warn("HMAC auth failed due to missing HTTP headers.")
        return False

    if content_md5 != hashlib.md5(request.body).hexdigest():
        logger.warn("HMAC auth failed due to incorrect Content-MD5 value.")
        return False

    # Check that the nonce value hasn't already been used, and remember it for
    # later.

    NonceValue.objects.purge()

    try:
        existing_nonce = NonceValue.objects.get(nonce=nonce)
    except NonceValue.DoesNotExist:
        existing_nonce = None

    if existing_nonce != None:
        logger.warn("HMAC auth failed because nonce value was reused.")
        return False

    nonce_value = NonceValue()
    nonce_value.nonce     = nonce
    nonce_value.timestamp = django.utils.timezone.now()
    nonce_value.save()

    # Calculate the HMAC-authentication digest, and check that it mathes the
    # digest value from the header.

    parts       = [request.method, request.path, content_md5,
                   nonce, account_secret]
    hmac_digest = hashlib.sha1("\n".join(parts)).hexdigest()
    hmac_base64 = base64.b64encode(hmac_digest)

    if hmac_auth_string != "HMAC " + hmac_base64:
        logger.warn("HMAC auth failed because authorization hash " +
                    "doesn't match.")
        return False

    # If we get here, the HMAC authentication succeeded.  Whew!

    return True

#############################################################################

def datetime_to_unix_timestamp(datetime_in_utc):
    """ Convert a datetime.datetime object (in UTC) into a unix timestamp.
    """
    unix_epoch = datetime.datetime(1970, 1, 1, tzinfo=timezone.utc)
    delta      = datetime_in_utc - unix_epoch
    return int(delta.seconds + delta.days * 86400)

#############################################################################

def date_to_string(date):
    """ Return a datetime.date() object as a string of the form "YYYY-MM-DD"

        If the given DateTime object is None, we return an empty string.
    """
    if date == None:
        return ""
    else:
        return date.strftime("%Y-%m-%d")

#############################################################################

def string_to_date(string):
    """ Return a string of the form "YYYY-MM-DD" as a datetime.date() object.

        If the given string can't be parsed into a valid date, we return None.
    """
    if string in ["", None]: return None

    parts = string.split("-")
    if len(parts) != 3: return None
    try:
        year = int(parts[0])
        month = int(parts[1])
        day = int(parts[2])
    except ValueError:
        return None

    if year < 1000 or year > 99999:
        return None

    if month < 1 or month > 12:
        return None

    if day < 1 or day > 31:
        return None

    return datetime.date(year, month, day)

#############################################################################

def exception_response():
    """ Return an HttpResponse object for when an exception occurs.

        This should be called when an exception was caught using try...except;
        we get the details of the exception, and return a short plain-text
        error message explaining what went wrong, wrapped in an HttpResponse
        object.

        If we are running the unit tests, we also print the exception to
        stderr, so the exception will be visible.
    """
    exception_type,exception_value,exception_tb = sys.exc_info()

    full_traceback = traceback.extract_tb(exception_tb)
    part_traceback = full_traceback[-2:] # Get last 2 items.

    error = []
    for line in traceback.format_list(part_traceback):
        error.append(line.rstrip())

    error.append(exception_type.__name__ + ":" + str(exception_value))

    if 'test' in sys.argv:
        print
        for line in error:
            print line
        print

    return HttpResponseServerError("\n".join(error))

