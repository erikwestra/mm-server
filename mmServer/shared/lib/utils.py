""" mmServer.shared.lib.utils

    This module define various utility functions used by the mmServer system.
"""
import base64
import hashlib
import logging
import random
import string
import uuid

from mmServer.shared.models import *

#############################################################################

logger = logging.getLogger(__name__)

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

def has_hmac_headers(request):
    """ Return True if the given request includes HMAC-authentication headers.
    """
    if "HTTP_AUTHORIZATION" not in request.META: return False
    if "HTTP_CONTENT_MD5"   not in request.META: return False
    if "HTTP_NONCE"         not in request.META: return False
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
    NonceValue.objects.purge()

    http_method      = request.method
    url              = request.path

    hmac_auth_string = request.META.get("HTTP_AUTHORIZATION")
    content_md5      = request.META.get("HTTP_CONTENT_MD5")
    nonce            = request.META.get("HTTP_NONCE")

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

