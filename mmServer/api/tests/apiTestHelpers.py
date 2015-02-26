""" mmServer.api.tests.apiTestHelpers

    This module defines various functions that simplify the process of testing
    the mmServer API.
"""
import base64
import uuid

from django.utils import timezone

import mock

from mmServer.shared.models import *
from mmServer.shared.lib    import utils, encryption

import mmServer.api.views.message

#############################################################################

def create_profile(name=None):
    """ Create and return a new Profile object.

        If a name is supplied, it will be used for the new profile.  Otherwise,
        a random name will be calculated.
    """
    global_id = utils.calc_unique_global_id()

    if name == None:
        name = utils.random_string()

    profile = Profile()
    profile.global_id                            = global_id
    profile.deleted                              = False
    profile.account_secret                       = utils.random_string()
    profile.name                                 = name
    profile.name_visible                         = True
    profile.email                                = utils.random_string()
    profile.phone                                = utils.random_string()
    profile.address_1                            = utils.random_string()
    profile.address_1_visible                    = False
    profile.address_2                            = utils.random_string()
    profile.address_2_visible                    = False
    profile.city                                 = utils.random_string()
    profile.city_visible                         = False
    profile.state_province_or_region             = utils.random_string()
    profile.state_province_or_region_visible     = False
    profile.zip_or_postal_code                   = utils.random_string()
    profile.zip_or_postal_code_visible           = False
    profile.country                              = utils.random_string()
    profile.country_visible                      = False
    profile.date_of_birth                        = datetime.date(1970, 01, 31)
    profile.social_security_number_last_4_digits = "1234"
    profile.bio                                  = utils.random_string()
    profile.bio_visible                          = False
    profile.picture_id                           = utils.random_string()
    profile.picture_id_visible                   = True
    profile.save()

    return profile

#############################################################################

def create_conversation(my_global_id, their_global_id,
                        hidden_1=False, hidden_2=False,
                        num_unread_1=0, num_unread_2=0):
    """ Create and return a new Conversation object.

        The conversation will be between the given two users, and can be hidden
        by setting the appropriate 'hidden_x' parameter to True.
    """
    conversation = Conversation()
    conversation.global_id_1    = my_global_id
    conversation.global_id_2    = their_global_id
    conversation.encryption_key = encryption.generate_random_key()
    conversation.hidden_1       = hidden_1
    conversation.hidden_2       = hidden_2
    conversation.last_message_1 = utils.random_string()
    conversation.last_message_2 = utils.random_string()
    conversation.last_timestamp = timezone.now()
    conversation.num_unread_1   = num_unread_1
    conversation.num_unread_2   = num_unread_2
    conversation.save()

    return conversation

#############################################################################

def create_picture():
    """ Create and return a new Picture object.
    """
    picture_data = utils.random_string(min_length=10000, max_length=20000)

    picture = Picture()
    picture.picture_id       = utils.calc_unique_picture_id()
    picture.account_secret   = utils.random_string()
    picture.picture_filename = utils.random_string() + ".png"
    picture.picture_data     = base64.b64encode(picture_data)
    picture.save()

    return picture

#############################################################################

def install_mock_ripple_interface():
    """ Replace rippleInterface.request() with a mock function.

        The mock function we install prevents the rippleInterface module from
        hitting the Ripple API while running a unit test.  The mock returns
        appropriate values to allow our code to sign, submit and retrieve
        payments.

        We prevent our API from hitting the Ripple network by replacing the
        mmServer.api.views.message.rippleInterface.request() function with a
        mock version.  We then return a copy of the mock object, so that our
        unit tests can check that the rippleInterface module was called by the
        API as it should be.
    """
    def rippleMockReturnValue(*args, **kwargs):
        if "command" in kwargs:
            command = kwargs['command']
        elif len(args) > 0:
            command = args[0]
        else:
            command = None

        if command == "sign":
            return {'status' : "success",
                    'type'   : "response",
                    'result' : {'tx_blob' : "BLOB"}}
        elif command == "submit":
            return {"status" : "success",
                    "type"   : "response",
                    "result" : {
                      "engine_result"         : "tesSUCCESS",
                      "engine_result_code"    : 0,
                      "engine_result_message" : "The transaction was " +
                                                "applied",
                      "tx_blob"               : "...",
                      "tx_json"               : {"hash"   : uuid.uuid4().hex,
                                                 "others" : "..."}
                    }
                   }
        elif command == "tx":
            return {'status' : "success",
                    'type'   : "response",
                    'result' : {
                        'validated' : True,
                        'status'    : "success",
                        'meta'      : {
                            'TransactionResult' : "tesSUCCESS",
                            'other'             : "...",
                        },
                        'other'     : "...",
                    }
                   }
        else:
            raise RuntimeError("Unexpected command:" + repr(command))

    rippleMock = mock.Mock(side_effect=rippleMockReturnValue)
    mmServer.api.views.message.rippleInterface.request = rippleMock

    return rippleMock

