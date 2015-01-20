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
                         'text'                 : message_text
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

        # Check that a PendingMessage record has been created for this
        # message.

        message = PendingMessage.objects.get(conversation=conversation)

        self.assertEqual(message.conversation, conversation)
        self.assertEqual(message.hash, tx_hash)
        self.assertIsNotNone(message.timestamp)
        self.assertEqual(message.sender_global_id, sender_profile.global_id)
        self.assertEqual(message.recipient_global_id,
                         recipient_profile.global_id)
        self.assertEqual(message.sender_account_id, sender_account_id)
        self.assertEqual(message.recipient_account_id, recipient_account_id)
        self.assertEqual(message.text, message_text)
        self.assertIsNone(message.last_status_check)

    # -----------------------------------------------------------------------

    def test_get_messages(self):
        """ Check that "GET api/messages" returns the user's messages.
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

        # Create some (finalized) test messages.

        message_1 = utils.random_string()
        message_2 = utils.random_string()
        message_3 = utils.random_string()

        for message_text in [message_1, message_2, message_3]:
            message = FinalMessage()
            message.conversation         = conversation
            message.hash                 = utils.random_string()
            message.timestamp            = timezone.now()
            message.sender_global_id     = sender_profile.global_id
            message.recipient_global_id  = recipient_profile.global_id
            message.sender_account_id    = sender_account_id
            message.recipient_account_id = recipient_account_id
            message.text                 = message_text
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
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], "application/json")
        data = json.loads(response.content)

        # Check that the list of messages was correctly returned.

        self.assertItemsEqual(data.keys(), ["messages", "next_anchor"])
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

        message = PendingMessage()
        message.conversation         = conversation
        message.hash                 = utils.random_string()
        message.timestamp            = timezone.now()
        message.sender_global_id     = sender_profile.global_id
        message.recipient_global_id  = recipient_profile.global_id
        message.sender_account_id    = sender_account_id
        message.recipient_account_id = recipient_account_id
        message.text                 = utils.random_string()
        message.last_status_check    = None
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
        # Ripple server, see that the message has been validated, and move it
        # into the list of finalized messages.

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

        # Check that the pending message has been deleted from the database.

        try:
            pending = PendingMessage.objects.get(id=message.id)
        except PendingMessage.DoesNotExist:
            pending = None

        self.assertIsNone(pending)

        # Check that the final version has been created in the database.

        try:
            final = FinalMessage.objects.get(conversation=conversation)
        except FinalMessage.DoesNotExist:
            final = None
        except FinalMessage.MultipleObjectsReturned:
            final = None

        self.assertIsNotNone(final)

        # Finally, check that the message details were copied across as
        # expected.

        self.assertEqual(final.conversation,        message.conversation)
        self.assertEqual(final.hash,                message.hash)
        self.assertEqual(final.timestamp,           message.timestamp)
        self.assertEqual(final.sender_global_id,    message.sender_global_id)
        self.assertEqual(final.recipient_global_id, message.recipient_global_id)
        self.assertEqual(final.sender_account_id,   message.sender_account_id)
        self.assertEqual(final.recipient_account_id,
                                                   message.recipient_account_id)
        self.assertEqual(final.text,                message.text)
        self.assertEqual(final.error,               None)

    # -----------------------------------------------------------------------

    def test_poll_for_new_messages(self):
        """ Check that we can poll for new messages using the "anchor" param.

            We create a series of messages, and call the "GET api/messages"
            endpoint to get the returned 'next_anchor' value.  We then add some
            more messages, and call the endpoint again with the supplied anchor
            to ensure that only the new messages are returned.
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

        # Create some (finalized) test messages.

        message_1 = utils.random_string()
        message_2 = utils.random_string()
        message_3 = utils.random_string()

        for message_text in [message_1, message_2, message_3]:
            message = FinalMessage()
            message.conversation         = conversation
            message.hash                 = utils.random_string()
            message.timestamp            = timezone.now()
            message.sender_global_id     = sender_profile.global_id
            message.recipient_global_id  = recipient_profile.global_id
            message.sender_account_id    = sender_account_id
            message.recipient_account_id = recipient_account_id
            message.text                 = message_text
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
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], "application/json")
        data = json.loads(response.content)

        # Get the 'next_anchor' value to use for our next request.

        next_anchor = data['next_anchor']

        # Now create two more finalized messages.

        message_4 = utils.random_string()
        message_5 = utils.random_string()

        for message_text in [message_4, message_5]:
            message = FinalMessage()
            message.conversation         = conversation
            message.hash                 = utils.random_string()
            message.timestamp            = timezone.now()
            message.sender_global_id     = sender_profile.global_id
            message.recipient_global_id  = recipient_profile.global_id
            message.sender_account_id    = sender_account_id
            message.recipient_account_id = recipient_account_id
            message.text                 = message_text
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

        # Ask the "GET api/messages" endpoint to return any new messages which
        # have come in since the 'last_anchor' value was calculated.

        url = "/api/messages?my_global_id=" + sender_profile.global_id \
            + "&their_global_id=" + recipient_profile.global_id \
            + "&anchor=" + next_anchor

        response = self.client.get(url,
                                   "",
                                   content_type="application/json",
                                   **headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], "application/json")
        data = json.loads(response.content)

        # Check that the updated messages were returned, as expected.

        self.assertItemsEqual(data.keys(), ["messages", "next_anchor"])
        self.assertEqual(len(data['messages']), 2)
        self.assertEqual(data['messages'][0]['text'], message_4)
        self.assertEqual(data['messages'][1]['text'], message_5)

