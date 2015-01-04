""" mmServer.api.views.profiles

    This module implements the "profiles" endpoint for the mmServer.api
    application.
"""
import logging

from django.http                  import *
from django.core.paginator        import *
from django.views.decorators.csrf import csrf_exempt

import simplejson as json

from mmServer.shared.models import *
from mmServer.shared.lib    import utils

#############################################################################

logger = logging.getLogger(__name__)

#############################################################################

@csrf_exempt
def endpoint(request):
    """ Respond to the "/api/profiles" endpoint.

        This view function simply selects an appropriate handler based on the
        HTTP method.
    """
    if request.method == "GET":
        return profiles_GET(request)
    else:
        return HttpResponseNotAllowed(["GET"])

#############################################################################

def profiles_GET(request):
    """ Respond to the "GET /api/profiles" API request.

        This is used to search for matching profiles.
    """
    # Extract our query-string parameters.

    if "name" in request.GET:
        name = request.GET['name']
    else:
        return HttpResponse(json.dumps({'success' : False,
                                        'error' : "Missing required 'name' " +
                                                  "parameter"}),
                            mimetype="application/json")

    if "page" in request.GET:
        page = request.GET['page']
    else:
        page = 1

    # Search for the matching profiles.

    query = Profile.objects.filter(name_visible=True,
                                   name__istartswith=name)
    profiles = Paginator(query, 50)

    # Check that the supplied page parameter is valid.

    try:
        page = int(page)
    except ValueError:
        return HttpResponse(json.dumps({'success' : False,
                                        'error' : "Invalid 'page' value"}),
                            mimetype="application/json")

    if page < 1 or page > profiles.num_pages:
        return HttpResponse(json.dumps({'success' : False,
                                        'error' : "Page out of range."}),
                            mimetype="application/json")

    # Extract the data to return from the matching profiles.

    results = {'success'   : True,
               'num_pages' : profiles.num_pages,
               'profiles'  : []}

    for profile in profiles.page(page):
        results['profiles'].append({'global_id' : profile.global_id,
                                    'name'      : profile.name})

    # Finally, return the results back to the caller.

    return HttpResponse(json.dumps(results),
                        mimetype="application/json")

