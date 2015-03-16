""" mmServer.shared.lib.rippleInterface

    This module handles the low-level communication between the mmServer system
    and a remote "rippled" server.
"""
import random

import websocket
import simplejson as json

from django.conf import settings

#############################################################################

def request(command, **params):
    """ Send a request to the rippled server, and wait for a response.

        If none of our configured servers will process the request, we return
        None.

        Note that this is a synchronous function; it waits for the server to
        respond before returning.  If something goes wrong, we try each server
        in turn until one works.  If no server returns a successful result, we
        return the last failed result.
    """
    servers = list(settings.RIPPLED_SERVER_URLS)
    random.shuffle(servers)

    last_response = False
    for server in servers:
        try:
            request = {'command' : command}
            request.update(params)

            socket = websocket.create_connection(server)
            socket.send(json.dumps(request))

            result = socket.recv()
            socket.close()
            response = json.loads(result)

            if response.get("status") == "success":
                return response
            else:
                # Keep trying with the next server.
                last_response = response
                continue
        except:
            continue

    return last_response

