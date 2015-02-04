""" mmServer.api.tests.test_messages

    This module implements various unit tests for the "message" resource's API
    endpoints.
"""

import base64
import logging
import random
import uuid

from django.utils import unittest, timezone
import django.test

import mock
import simplejson as json

from mmServer.shared.models import *
from mmServer.shared.lib    import utils, encryption

import mmServer.api.views.message

#############################################################################

class MessageTestCase(django.test.TestCase):
    """ Unit tests for the "Message" resource.
    """
    def test_send_message(self):
        """ Test the logic of sending a message via the API.
        """
        # Create a profile for the sender.

        sender_profile = Profile()
        sender_profile.global_id        = utils.calc_unique_global_id()
        sender_profile.account_secret   = utils.random_string()
        sender_profile.name             = utils.random_string()
        sender_profile.name_visible     = True
        sender_profile.location         = utils.random_string()
        sender_profile.location_visible = False
        sender_profile.picture_id       = utils.random_string()
        sender_profile.picture_visible  = True
        sender_profile.save()

        # Create a profile for the recipient.

        recipient_profile = Profile()
        recipient_profile.global_id        = utils.calc_unique_global_id()
        recipient_profile.account_secret   = utils.random_string()
        recipient_profile.name             = utils.random_string()
        recipient_profile.name_visible     = True
        recipient_profile.location         = utils.random_string()
        recipient_profile.location_visible = False
        recipient_profile.picture_id       = utils.random_string()
        recipient_profile.picture_visible  = True
        recipient_profile.save()

        # Create two random Ripple account IDs.

        sender_account_id    = utils.random_string()
        recipient_account_id = utils.random_string()

        # Create a conversation between these two users.

        conversation = Conversation()
        conversation.global_id_1    = sender_profile.global_id
        conversation.global_id_2    = recipient_profile.global_id
        conversation.hidden_1       = False
        conversation.hidden_2       = False
        conversation.encryption_key = encryption.generate_random_key()
        conversation.last_message   = utils.random_string()
        conversation.last_timestamp = timezone.now()
        conversation.num_unread_1   = 0
        conversation.num_unread_2   = 0

        conversation.save()

        # Create the body of our request.

        message_text = utils.random_string()

        request = json.dumps(
                        {'sender_global_id'     : sender_profile.global_id,
                         'recipient_global_id'  : recipient_profile.global_id,
                         'sender_account_id'    : sender_account_id,
                         'recipient_account_id' : recipient_account_id,
                         'text'                 : message_text,
                        })

        # Calculate the HMAC authentication headers we need to make an
        # authenticated request.

        headers = utils.calc_hmac_headers(
            method="POST",
            url="/api/message",
            body=request,
            account_secret=sender_profile.account_secret
        )

        # Setup a mock version of the rippleInterface.request() function.  This
        # replaces the call to rippleInterface.request() in our view function
        # so the API doesn't actually send the message to the Ripple network.

        tx_hash = uuid.uuid4().hex

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
                          "tx_json"               : {"hash" : tx_hash,
                                                     "others" : "..."}
                        }
                       }
            else:
                raise RuntimeError("Unexpected command!")

        rippleMock = mock.Mock(side_effect=rippleMockReturnValue)
        mmServer.api.views.message.rippleInterface.request = rippleMock

        # Ask the "POST /api/message" endpoint to create the message.

        response = self.client.post("/api/message",
                                    request,
                                    content_type="application/json",
                                    **headers)
        self.assertEqual(response.status_code, 202)

        # Check that the rippleInterface.request() function was called to sign
        # and then submit the message.

        self.assertEqual(rippleMock.call_count, 2)
        self.assertEqual(rippleMock.call_args_list[0][0][0], "sign")
        self.assertEqual(rippleMock.call_args_list[1][0][0], "submit")

        # Check that a Message record has been created for this message.

        message = Message.objects.get(conversation=conversation)

        self.assertIsNotNone(message.update_id)
        self.assertEqual(message.conversation, conversation)
        self.assertEqual(message.hash, tx_hash)
        self.assertIsNotNone(message.timestamp)
        self.assertEqual(message.sender_global_id, sender_profile.global_id)
        self.assertEqual(message.recipient_global_id,
                         recipient_profile.global_id)
        self.assertEqual(message.sender_account_id, sender_account_id)
        self.assertEqual(message.recipient_account_id, recipient_account_id)
        self.assertEqual(message.text, message_text)
        self.assertIsNone(message.action)
        self.assertIsNone(message.action_params)
        self.assertEqual(message.amount_in_drops, 1)
        self.assertEqual(message.status, Message.STATUS_PENDING)
        self.assertIsNone(message.error)

    # -----------------------------------------------------------------------

    def test_send_message_with_action(self):
        """ Test the logic of sending a message with an attached action.
        """
        # Create a profile for the sender.

        sender_profile = Profile()
        sender_profile.global_id        = utils.calc_unique_global_id()
        sender_profile.account_secret   = utils.random_string()
        sender_profile.name             = utils.random_string()
        sender_profile.name_visible     = True
        sender_profile.location         = utils.random_string()
        sender_profile.location_visible = False
        sender_profile.picture_id       = utils.random_string()
        sender_profile.picture_visible  = True
        sender_profile.save()

        # Create a profile for the recipient.

        recipient_profile = Profile()
        recipient_profile.global_id        = utils.calc_unique_global_id()
        recipient_profile.account_secret   = utils.random_string()
        recipient_profile.name             = utils.random_string()
        recipient_profile.name_visible     = True
        recipient_profile.location         = utils.random_string()
        recipient_profile.location_visible = False
        recipient_profile.picture_id       = utils.random_string()
        recipient_profile.picture_visible  = True
        recipient_profile.save()

        # Create two random Ripple account IDs.

        sender_account_id    = utils.random_string()
        recipient_account_id = utils.random_string()

        # Create a conversation between these two users.

        conversation = Conversation()
        conversation.global_id_1    = sender_profile.global_id
        conversation.global_id_2    = recipient_profile.global_id
        conversation.hidden_1       = False
        conversation.hidden_2       = False
        conversation.encryption_key = encryption.generate_random_key()
        conversation.last_message   = utils.random_string()
        conversation.last_timestamp = timezone.now()
        conversation.num_unread_1   = 0
        conversation.num_unread_2   = 0

        conversation.save()

        # Create the body of our request.

        message_text = utils.random_string()

        request = json.dumps(
                        {'sender_global_id'     : sender_profile.global_id,
                         'recipient_global_id'  : recipient_profile.global_id,
                         'sender_account_id'    : sender_account_id,
                         'recipient_account_id' : recipient_account_id,
                         'text'                 : message_text,
                         'action'               : "SEND_XRP",
                         'action_params'        : json.dumps({'amount' : 10}),
                         'amount_in_drops'      : 10,
                        })

        # Calculate the HMAC authentication headers we need to make an
        # authenticated request.

        headers = utils.calc_hmac_headers(
            method="POST",
            url="/api/message",
            body=request,
            account_secret=sender_profile.account_secret
        )

        # Setup a mock version of the rippleInterface.request() function.  This
        # replaces the call to rippleInterface.request() in our view function
        # so the API doesn't actually send the message to the Ripple network.

        tx_hash = uuid.uuid4().hex

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
                          "tx_json"               : {"hash" : tx_hash,
                                                     "others" : "..."}
                        }
                       }
            else:
                raise RuntimeError("Unexpected command!")

        rippleMock = mock.Mock(side_effect=rippleMockReturnValue)
        mmServer.api.views.message.rippleInterface.request = rippleMock

        # Ask the "POST /api/message" endpoint to create the message.

        response = self.client.post("/api/message",
                                    request,
                                    content_type="application/json",
                                    **headers)
        self.assertEqual(response.status_code, 202)

        # Check that the rippleInterface.request() function was called to sign
        # and then submit the message.

        self.assertEqual(rippleMock.call_count, 2)
        self.assertEqual(rippleMock.call_args_list[0][0][0], "sign")
        self.assertEqual(rippleMock.call_args_list[1][0][0], "submit")

        # Check that a Message record has been created for this message.

        message = Message.objects.get(conversation=conversation)

        self.assertIsNotNone(message.update_id)
        self.assertEqual(message.conversation, conversation)
        self.assertEqual(message.hash, tx_hash)
        self.assertIsNotNone(message.timestamp)
        self.assertEqual(message.sender_global_id, sender_profile.global_id)
        self.assertEqual(message.recipient_global_id,
                         recipient_profile.global_id)
        self.assertEqual(message.sender_account_id, sender_account_id)
        self.assertEqual(message.recipient_account_id, recipient_account_id)
        self.assertEqual(message.text, message_text)
        self.assertEqual(message.action, "SEND_XRP")
        self.assertEqual(message.action_params, json.dumps({'amount' : 10}))
        self.assertEqual(message.amount_in_drops, 10)
        self.assertEqual(message.status, Message.STATUS_PENDING)
        self.assertIsNone(message.error)

    # -----------------------------------------------------------------------

    def test_update_message(self):
        """ Check that the "PUT api/message" message updates a message.
        """
        # Create a profile for the sender.

        sender_profile = Profile()
        sender_profile.global_id        = utils.calc_unique_global_id()
        sender_profile.account_secret   = utils.random_string()
        sender_profile.name             = utils.random_string()
        sender_profile.name_visible     = True
        sender_profile.location         = utils.random_string()
        sender_profile.location_visible = False
        sender_profile.picture_id       = utils.random_string()
        sender_profile.picture_visible  = True
        sender_profile.save()

        # Create a profile for the recipient.

        recipient_profile = Profile()
        recipient_profile.global_id        = utils.calc_unique_global_id()
        recipient_profile.account_secret   = utils.random_string()
        recipient_profile.name             = utils.random_string()
        recipient_profile.name_visible     = True
        recipient_profile.location         = utils.random_string()
        recipient_profile.location_visible = False
        recipient_profile.picture_id       = utils.random_string()
        recipient_profile.picture_visible  = True
        recipient_profile.save()

        # Create a conversation between these two users.

        conversation = Conversation()
        conversation.global_id_1    = sender_profile.global_id
        conversation.global_id_2    = recipient_profile.global_id
        conversation.hidden_1       = False
        conversation.hidden_2       = False
        conversation.encryption_key = encryption.generate_random_key()
        conversation.last_message   = utils.random_string()
        conversation.last_timestamp = timezone.now()
        conversation.num_unread_1   = 0
        conversation.num_unread_2   = 0

        conversation.save()

        # Create random Ripple account IDs for our two users.

        sender_account_id    = utils.random_string()
        recipient_account_id = utils.random_string()

        # Create a test message with an embedded action.

        message = Message()
        message.conversation         = conversation
        message.hash                 = utils.random_string()
        message.timestamp            = timezone.now()
        message.sender_global_id     = sender_profile.global_id
        message.recipient_global_id  = recipient_profile.global_id
        message.sender_account_id    = sender_account_id
        message.recipient_account_id = recipient_account_id
        message.text                 = "SEND 1 XRP"
        message.status               = Message.STATUS_SENT
        message.action               = "SEND_XRP"
        message.action_params        = json.dumps({'amount' : 1000000})
        message.action_processed     = False
        message.amount_in_drops      = 1000000
        message.error                = None
        message.save()

        # Prepare the body of our request.

        request = json.dumps({'message' : {'hash'      : message.hash,
                                           'processed' : True,
                                           'read'      : True}})

        # Calculate the HMAC authentication headers we need to make an
        # authenticated request.

        headers = utils.calc_hmac_headers(
            method="PUT",
            url="/api/message",
            body=request,
            account_secret=recipient_profile.account_secret
        )

        # Ask the "PUT /api/message" endpoint to update the message.

        response = self.client.put("/api/message",
                                   request,
                                   content_type="application/json",
                                   **headers)
        self.assertEqual(response.status_code, 200)

        # Check that the message was updated appropriately.

        msg = Message.objects.get(conversation=conversation)
        self.assertEqual(msg.action_processed, True)
        self.assertEqual(msg.status,           Message.STATUS_READ)

    # -----------------------------------------------------------------------

    def test_get_all_messages(self):
        """ Check that "GET api/messages" returns all of a user's messages.
        """
        # Create a profile for the current user.

        my_profile = Profile()
        my_profile.global_id        = utils.calc_unique_global_id()
        my_profile.account_secret   = utils.random_string()
        my_profile.name             = utils.random_string()
        my_profile.name_visible     = True
        my_profile.location         = utils.random_string()
        my_profile.location_visible = False
        my_profile.picture_id       = utils.random_string()
        my_profile.picture_visible  = True
        my_profile.save()

        # Create profile for two other users the current user is communicating
        # with.

        other_profile_1 = Profile()
        other_profile_1.global_id        = utils.calc_unique_global_id()
        other_profile_1.account_secret   = utils.random_string()
        other_profile_1.name             = utils.random_string()
        other_profile_1.name_visible     = True
        other_profile_1.location         = utils.random_string()
        other_profile_1.location_visible = False
        other_profile_1.picture_id       = utils.random_string()
        other_profile_1.picture_visible  = True
        other_profile_1.save()

        other_profile_2 = Profile()
        other_profile_2.global_id        = utils.calc_unique_global_id()
        other_profile_2.account_secret   = utils.random_string()
        other_profile_2.name             = utils.random_string()
        other_profile_2.name_visible     = True
        other_profile_2.location         = utils.random_string()
        other_profile_2.location_visible = False
        other_profile_2.picture_id       = utils.random_string()
        other_profile_2.picture_visible  = True
        other_profile_2.save()

        # Create a conversation between the current user and other user 1.

        conversation_1 = Conversation()
        conversation_1.global_id_1    = my_profile.global_id
        conversation_1.global_id_2    = other_profile_1.global_id
        conversation_1.hidden_1       = False
        conversation_1.hidden_2       = False
        conversation_1.encryption_key = encryption.generate_random_key()
        conversation_1.last_message   = utils.random_string()
        conversation_1.last_timestamp = timezone.now()
        conversation_1.num_unread_1   = 0
        conversation_1.num_unread_2   = 0

        conversation_1.save()

        # Create a conversation between the current user and other user 2.

        conversation_2 = Conversation()
        conversation_2.global_id_1    = my_profile.global_id
        conversation_2.global_id_2    = other_profile_2.global_id
        conversation_2.hidden_1       = False
        conversation_2.hidden_2       = False
        conversation_2.encryption_key = encryption.generate_random_key()
        conversation_2.last_message   = utils.random_string()
        conversation_2.last_timestamp = timezone.now()
        conversation_2.num_unread_1   = 0
        conversation_2.num_unread_2   = 0

        conversation_2.save()

        # Create random Ripple account IDs for our three users.

        my_account_id      = utils.random_string()
        other_account_id_1 = utils.random_string()
        other_account_id_2 = utils.random_string()

        # Create a bunch of messages between the three users.

        messages = [{'conversation'      : conversation_1,
                     'sender_id'         : my_profile.global_id,
                     'sender_account'    : my_account_id,
                     'recipient_id'      : other_profile_1.global_id,
                     'recipient_account' : other_account_id_1,
                     'text'              : utils.random_string()},

                    {'conversation'      : conversation_1,
                     'sender_id'         : other_profile_1.global_id,
                     'sender_account'    : other_account_id_1,
                     'recipient_id'      : my_profile.global_id,
                     'recipient_account' : my_account_id,
                     'text'              : utils.random_string()},

                    {'conversation'      : conversation_2,
                     'sender_id'         : my_profile.global_id,
                     'sender_account'    : my_account_id,
                     'recipient_id'      : other_profile_2.global_id,
                     'recipient_account' : other_account_id_2,
                     'text'              : utils.random_string()},

                    {'conversation'      : conversation_2,
                     'sender_id'         : other_profile_2.global_id,
                     'sender_account'    : other_account_id_2,
                     'recipient_id'      : my_profile.global_id,
                     'recipient_account' : my_account_id,
                     'text'              : utils.random_string()}]

        for msg in messages:
            message = Message()
            message.conversation         = msg['conversation']
            message.hash                 = utils.random_string()
            message.timestamp            = timezone.now()
            message.sender_global_id     = msg['sender_id']
            message.recipient_global_id  = msg['recipient_id']
            message.sender_account_id    = msg['sender_account']
            message.recipient_account_id = msg['recipient_account']
            message.text                 = msg['text']
            message.status               = Message.STATUS_SENT
            message.action               = None
            message.action_params        = json.dumps({})
            message.amount_in_drops      = 1
            message.error                = None
            message.save()

        # Calculate the HMAC authentication headers we need to make an
        # authenticated request.

        headers = utils.calc_hmac_headers(
            method="GET",
            url="/api/messages",
            body="",
            account_secret=my_profile.account_secret
        )

        # Ask the "GET api/messages" endpoint to return the list of messages
        # between these two users.

        url = "/api/messages?my_global_id=" + my_profile.global_id
        response = self.client.get(url,
                                   "",
                                   content_type="application/json",
                                   **headers)
        if response.status_code == 500:
            print response.content

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], "application/json")
        data = json.loads(response.content)

        # Check that the list of messages was correctly returned.

        self.assertItemsEqual(data.keys(), ["messages"])
        self.assertEqual(len(data['messages']), 4)
        self.assertEqual(data['messages'][0]['text'], messages[0]['text'])
        self.assertEqual(data['messages'][1]['text'], messages[1]['text'])
        self.assertEqual(data['messages'][2]['text'], messages[2]['text'])
        self.assertEqual(data['messages'][3]['text'], messages[3]['text'])

    # -----------------------------------------------------------------------

    def test_get_conversation_messages(self):
        """ Check that "GET api/messages" returns messages between two users.
        """
        # Create a profile for the sender.

        sender_profile = Profile()
        sender_profile.global_id        = utils.calc_unique_global_id()
        sender_profile.account_secret   = utils.random_string()
        sender_profile.name             = utils.random_string()
        sender_profile.name_visible     = True
        sender_profile.location         = utils.random_string()
        sender_profile.location_visible = False
        sender_profile.picture_id       = utils.random_string()
        sender_profile.picture_visible  = True
        sender_profile.save()

        # Create a profile for the recipient.

        recipient_profile = Profile()
        recipient_profile.global_id        = utils.calc_unique_global_id()
        recipient_profile.account_secret   = utils.random_string()
        recipient_profile.name             = utils.random_string()
        recipient_profile.name_visible     = True
        recipient_profile.location         = utils.random_string()
        recipient_profile.location_visible = False
        recipient_profile.picture_id       = utils.random_string()
        recipient_profile.picture_visible  = True
        recipient_profile.save()

        # Create a conversation between these two users.

        conversation = Conversation()
        conversation.global_id_1    = sender_profile.global_id
        conversation.global_id_2    = recipient_profile.global_id
        conversation.hidden_1       = False
        conversation.hidden_2       = False
        conversation.encryption_key = encryption.generate_random_key()
        conversation.last_message   = utils.random_string()
        conversation.last_timestamp = timezone.now()
        conversation.num_unread_1   = 0
        conversation.num_unread_2   = 0

        conversation.save()

        # Create random Ripple account IDs for our two users.

        sender_account_id    = utils.random_string()
        recipient_account_id = utils.random_string()

        # Create some test messages.

        message_1 = utils.random_string()
        message_2 = utils.random_string()
        message_3 = utils.random_string()

        for message_text in [message_1, message_2, message_3]:
            message = Message()
            message.conversation         = conversation
            message.hash                 = utils.random_string()
            message.timestamp            = timezone.now()
            message.sender_global_id     = sender_profile.global_id
            message.recipient_global_id  = recipient_profile.global_id
            message.sender_account_id    = sender_account_id
            message.recipient_account_id = recipient_account_id
            message.text                 = message_text
            message.status               = Message.STATUS_SENT
            message.action               = "SEND_XRP"
            message.action_params        = json.dumps({'amount' : 10})
            message.amount_in_drops      = 10
            message.error                = None
            message.save()

        # Calculate the HMAC authentication headers we need to make an
        # authenticated request.

        headers = utils.calc_hmac_headers(
            method="GET",
            url="/api/messages",
            body="",
            account_secret=sender_profile.account_secret
        )

        # Ask the "GET api/messages" endpoint to return the list of messages
        # between these two users.

        url = "/api/messages?my_global_id=" + sender_profile.global_id \
            + "&their_global_id=" + recipient_profile.global_id
        response = self.client.get(url,
                                   "",
                                   content_type="application/json",
                                   **headers)
        if response.status_code == 500:
            print response.content

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], "application/json")
        data = json.loads(response.content)

        # Check that the list of messages was correctly returned.

        self.assertItemsEqual(data.keys(), ["messages"])
        self.assertEqual(len(data['messages']), 3)
        self.assertEqual(data['messages'][0]['text'], message_1)
        self.assertEqual(data['messages'][1]['text'], message_2)
        self.assertEqual(data['messages'][2]['text'], message_3)

    # -----------------------------------------------------------------------

    def test_get_messages_finalizes_pending_message(self):
        """ Check that "GET api/messages" finalizes pending messages.

            We create a pending message, and then make a "GET api/messages"
            call, mocking out the Ripple interface to pretend that the message
            was accepted into the Ripple ledger.  We check to ensure that the
            pending message is finalized and appears in the list of final
            messages.
        """
        # Create a profile for the sender.

        sender_profile = Profile()
        sender_profile.global_id        = utils.calc_unique_global_id()
        sender_profile.account_secret   = utils.random_string()
        sender_profile.name             = utils.random_string()
        sender_profile.name_visible     = True
        sender_profile.location         = utils.random_string()
        sender_profile.location_visible = False
        sender_profile.picture_id       = utils.random_string()
        sender_profile.picture_visible  = True
        sender_profile.save()

        # Create a profile for the recipient.

        recipient_profile = Profile()
        recipient_profile.global_id        = utils.calc_unique_global_id()
        recipient_profile.account_secret   = utils.random_string()
        recipient_profile.name             = utils.random_string()
        recipient_profile.name_visible     = True
        recipient_profile.location         = utils.random_string()
        recipient_profile.location_visible = False
        recipient_profile.picture_id       = utils.random_string()
        recipient_profile.picture_visible  = True
        recipient_profile.save()

        # Create a conversation between these two users.

        conversation = Conversation()
        conversation.global_id_1    = sender_profile.global_id
        conversation.global_id_2    = recipient_profile.global_id
        conversation.hidden_1       = False
        conversation.hidden_2       = False
        conversation.encryption_key = encryption.generate_random_key()
        conversation.last_message   = utils.random_string()
        conversation.last_timestamp = timezone.now()
        conversation.num_unread_1   = 0
        conversation.num_unread_2   = 0

        conversation.save()

        # Create random Ripple account IDs for our two users.

        sender_account_id    = utils.random_string()
        recipient_account_id = utils.random_string()

        # Create a dummy pending message.

        message = Message()
        message.conversation         = conversation
        message.hash                 = utils.random_string()
        message.timestamp            = timezone.now()
        message.sender_global_id     = sender_profile.global_id
        message.recipient_global_id  = recipient_profile.global_id
        message.sender_account_id    = sender_account_id
        message.recipient_account_id = recipient_account_id
        message.text                 = utils.random_string()
        message.status               = Message.STATUS_PENDING
        message.error                = None
        message.save()

        # Calculate the HMAC authentication headers we need to make an
        # authenticated request.

        headers = utils.calc_hmac_headers(
            method="GET",
            url="/api/messages",
            body="",
            account_secret=sender_profile.account_secret
        )

        # Setup a mock version of the rippleInterface.request() function.  This
        # replaces the call to rippleInterface.request() in our view function
        # so the API doesn't actually ask the Ripple network for the status of
        # the message.

        tx_hash = uuid.uuid4().hex

        def rippleMockReturnValue(*args, **kwargs):
            if "command" in kwargs:
                command = kwargs['command']
            elif len(args) > 0:
                command = args[0]
            else:
                command = None

            if command == "tx":
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
                raise RuntimeError("Unexpected command!")

        rippleMock = mock.Mock(side_effect=rippleMockReturnValue)
        mmServer.api.views.message.rippleInterface.request = rippleMock

        # Ask the "GET api/messages" endpoint to return the messages for this
        # conversation.  All going well, the endpoint should check with the
        # Ripple server, see that the message has been validated, and change
        # the message status to "sent".

        url = "/api/messages?my_global_id=" + sender_profile.global_id \
            + "&their_global_id=" + recipient_profile.global_id
        response = self.client.get(url,
                                   "",
                                   content_type="application/json",
                                   **headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], "application/json")

        # Check that the rippleInterface.request() function was called to check
        # the transaction status.

        self.assertEqual(rippleMock.call_count, 1)
        rippleMock.assert_called_once_with('tx',
                                           transaction=message.hash,
                                           binary=False)

        # Get the updated Message record.

        msg = Message.objects.get(conversation=conversation)
        self.assertIsNotNone(msg)

        # Finally, check that the message details were updated appropriately.

        self.assertEqual(msg.status, Message.STATUS_SENT)
        self.assertEqual(msg.error,  None)

