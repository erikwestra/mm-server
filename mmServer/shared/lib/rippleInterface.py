""" mmServer.shared.lib.rippleInterface

    This module handles the low-level communication between the mmServer system
    and a remote "rippled" server.
"""
import websocket
import simplejson as json

from django.conf import settings

#############################################################################

def request(command, **params):
    """ Send a request to the rippled server, and wait for a response.

        Note that this is a synchronous function; it waits for the server to
        respond before returning.
    """
    request = {'command' : command}
    request.update(params)

    socket = websocket.create_connection(settings.RIPPLED_SERVER_URL)
    socket.send(json.dumps(request))

    result = socket.recv()
    socket.close()
    return json.loads(result)

