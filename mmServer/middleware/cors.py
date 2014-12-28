""" middleware.cors.py

    This middleware component enables CORS (Cross-Origin Resource Sharing) for
    incoming requests.

    For information on the CORS standard, please refer to:

        http://enable-cors.org

    This middleware component uses the following settings:

        CORS_ALLOWED_METHODS

            A comma-separated list of HTTP methods allowed by the CORS
            middleware.  Defaults to "GET, POST, OPTIONS" if not specified.

        CORS_ALLOWED_HEADERS

            A comma-separated list of HTTP headers allowed by the CORS
            middleware.  Defaults to "Content-Type" if not specified.

    You should override these in your settings.py module if your application
    accepts a different set of HTTP methods or headers.
"""
from django.http import HttpResponse
from django.conf import settings

#############################################################################

class CORSMiddleware(object):
    """ Middleware component to enable CORS support for all incoming requests.

        This class is derived from:

            https://github.com/elevenbasetwo/django-cors.
    """
    def process_request(self, request):
        """ Respond to an incoming HTTP request.

            We return a blank response to an OPTIONS request, as defined by the
            CORS standard to "preflight" the request.
        """
        if request.method == 'OPTIONS':
            return HttpResponse()


    def process_response(self, request, response):
        """ Add the CORS headers to our HTTP response.
        """
        origin = request.META.get('HTTP_ORIGIN')
        if origin:
            allowed_methods = getattr(settings, "CORS_ALLOWED_METHODS",
                                      "GET, POST, OPTIONS")
            allowed_headers = getattr(settings, "CORS_ALLOWED_HEADERS",
                                      "Content-Type")
            response['Access-Control-Allow-Origin']  = origin
            response['Access-Control-Allow-Methods'] = allowed_methods
            response['Access-Control-Allow-Headers'] = allowed_headers
        return response

