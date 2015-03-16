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

import simplejson as json

from mmServer.shared.models import *
from mmServer.shared.lib    import utils

from mmServer.api.tests import apiTestHelpers

#############################################################################

class MessageTestCase(django.test.TestCase):
    """ Unit tests for the "Message" resource.
    """
    def test_send_message(self):
        """ Test the logic of sending a message via the API.
        """
        # Create two random profiles.

        sender_profile    = apiTestHelpers.create_profile()
        recipient_profile = apiTestHelpers.create_profile()

        # Create two random Ripple account IDs.

        sender_account_id    = utils.random_string()
        recipient_account_id = utils.random_string()

        # Create a conversation between these two users.

        conversation = \
            apiTestHelpers.create_conversation(sender_profile.global_id,
                                               recipient_profile.global_id)

        # Create the body of our request.

        sender_text    = utils.random_string()
        recipient_text = utils.random_string()

        request = json.dumps(
                        {'sender_global_id'     : sender_profile.global_id,
                         'recipient_global_id'  : recipient_profile.global_id,
                         'sender_account_id'    : sender_account_id,
                         'recipient_account_id' : recipient_account_id,
                         'sender_text'          : sender_text,
                         'recipient_text'       : recipient_text,
                        })

        # Calculate the HMAC authentication headers we need to make an
        # authenticated request.

        headers = utils.calc_hmac_headers(
            method="POST",
            url="/api/message",
            body=request,
            account_secret=sender_profile.account_secret
        )

        # Install the mock version of the rippleInterface.request() function.
        # This prevents the rippleInterface module from submitting a message to
        # the Ripple network.

        rippleMock = apiTestHelpers.install_mock_ripple_interface()

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
        self.assertIsNotNone(message.hash)
        self.assertIsNotNone(message.timestamp)
        self.assertEqual(message.sender_global_id, sender_profile.global_id)
        self.assertEqual(message.recipient_global_id,
                         recipient_profile.global_id)
        self.assertEqual(message.sender_account_id, sender_account_id)
        self.assertEqual(message.recipient_account_id, recipient_account_id)
        self.assertEqual(message.sender_text, sender_text)
        self.assertEqual(message.recipient_text, recipient_text)
        self.assertIsNone(message.action)
        self.assertIsNone(message.action_params)
        self.assertEqual(message.amount_in_drops, 1)
        self.assertEqual(message.status, Message.STATUS_PENDING)
        self.assertIsNone(message.error)

    # -----------------------------------------------------------------------

    def test_send_message_with_action(self):
        """ Test the logic of sending a message with an attached action.
        """
        # Create two random profiles for testing.

        sender_profile    = apiTestHelpers.create_profile()
        recipient_profile = apiTestHelpers.create_profile()

        # Create two random Ripple account IDs.

        sender_account_id    = utils.random_string()
        recipient_account_id = utils.random_string()

        # Create a conversation between these two users.

        conversation = \
            apiTestHelpers.create_conversation(sender_profile.global_id,
                                               recipient_profile.global_id)

        # Create the body of our request.

        sender_text    = utils.random_string()
        recipient_text = utils.random_string()

        request = json.dumps(
                        {'sender_global_id'     : sender_profile.global_id,
                         'recipient_global_id'  : recipient_profile.global_id,
                         'sender_account_id'    : sender_account_id,
                         'recipient_account_id' : recipient_account_id,
                         'sender_text'          : sender_text,
                         'recipient_text'       : recipient_text,
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

        # Install the mock version of the rippleInterface.request() function.
        # This prevents the rippleInterface module from submitting a message to
        # the Ripple network.

        rippleMock = apiTestHelpers.install_mock_ripple_interface()

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
        self.assertIsNotNone(message.hash)
        self.assertIsNotNone(message.timestamp)
        self.assertEqual(message.sender_global_id, sender_profile.global_id)
        self.assertEqual(message.recipient_global_id,
                         recipient_profile.global_id)
        self.assertEqual(message.sender_account_id, sender_account_id)
        self.assertEqual(message.recipient_account_id, recipient_account_id)
        self.assertEqual(message.sender_text, sender_text)
        self.assertEqual(message.recipient_text, recipient_text)
        self.assertEqual(message.action, "SEND_XRP")
        self.assertEqual(message.action_params, json.dumps({'amount' : 10}))
        self.assertEqual(message.amount_in_drops, 10)
        self.assertEqual(message.status, Message.STATUS_PENDING)
        self.assertIsNone(message.error)

    # -----------------------------------------------------------------------

    def test_update_message(self):
        """ Check that the "PUT api/message" message updates a message.
        """
        # Create two profiles, for testing.

        sender_profile    = apiTestHelpers.create_profile()
        recipient_profile = apiTestHelpers.create_profile()

        # Create a conversation between these two users.

        conversation = \
            apiTestHelpers.create_conversation(sender_profile.global_id,
                                               recipient_profile.global_id)

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
        message.sender_text          = "SEND 1 XRP"
        message.recipient_text       = "RECEIVED 1 XRP"
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

        my_profile = apiTestHelpers.create_profile()

        # Create profile for two other users the current user is communicating
        # with.

        other_profile_1 = apiTestHelpers.create_profile()
        other_profile_2 = apiTestHelpers.create_profile()

        # Create a conversation between the current user and other user 1.

        conversation_1 = \
            apiTestHelpers.create_conversation(my_profile.global_id,
                                               other_profile_1.global_id)

        # Create a conversation between the current user and other user 2.

        conversation_2 = \
            apiTestHelpers.create_conversation(my_profile.global_id,
                                               other_profile_2.global_id)

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
                     'sender_text'       : utils.random_string(),
                     'recipient_text'    : utils.random_string()},

                    {'conversation'      : conversation_1,
                     'sender_id'         : other_profile_1.global_id,
                     'sender_account'    : other_account_id_1,
                     'recipient_id'      : my_profile.global_id,
                     'recipient_account' : my_account_id,
                     'sender_text'       : utils.random_string(),
                     'recipient_text'    : utils.random_string()},

                    {'conversation'      : conversation_2,
                     'sender_id'         : my_profile.global_id,
                     'sender_account'    : my_account_id,
                     'recipient_id'      : other_profile_2.global_id,
                     'recipient_account' : other_account_id_2,
                     'sender_text'       : utils.random_string(),
                     'recipient_text'    : utils.random_string()},

                    {'conversation'      : conversation_2,
                     'sender_id'         : other_profile_2.global_id,
                     'sender_account'    : other_account_id_2,
                     'recipient_id'      : my_profile.global_id,
                     'recipient_account' : my_account_id,
                     'sender_text'       : utils.random_string(),
                     'recipient_text'    : utils.random_string()}]

        for msg in messages:
            message = Message()
            message.conversation         = msg['conversation']
            message.hash                 = utils.random_string()
            message.timestamp            = timezone.now()
            message.sender_global_id     = msg['sender_id']
            message.recipient_global_id  = msg['recipient_id']
            message.sender_account_id    = msg['sender_account']
            message.recipient_account_id = msg['recipient_account']
            message.sender_text          = msg['sender_text']
            message.recipient_text       = msg['recipient_text']
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
        # for this user.

        url = "/api/messages?my_global_id=%s&num_msgs=-1" % my_profile.global_id

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

        self.assertItemsEqual(data.keys(), ["messages", "has_more"])
        self.assertEqual(len(data['messages']), len(messages))
        for i in range(len(messages)):
            orig_msg     = messages[i]
            returned_msg = data['messages'][i]

            self.assertEqual(orig_msg['sender_text'],
                             returned_msg['sender_text'])
            self.assertEqual(orig_msg['recipient_text'],
                             returned_msg['recipient_text'])

    # -----------------------------------------------------------------------

    def test_get_paginated_messages(self):
        """ Check that "GET api/messages" returns all of a user's messages.
        """
        # Create a profile for the current user.

        my_profile = apiTestHelpers.create_profile()

        # Create profile for two other users the current user is communicating
        # with.

        other_profile_1 = apiTestHelpers.create_profile()
        other_profile_2 = apiTestHelpers.create_profile()

        # Create a conversation between the current user and other user 1.

        conversation_1 = \
            apiTestHelpers.create_conversation(my_profile.global_id,
                                               other_profile_1.global_id)

        # Create a conversation between the current user and other user 2.

        conversation_2 = \
            apiTestHelpers.create_conversation(my_profile.global_id,
                                               other_profile_2.global_id)

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
                     'sender_text'       : utils.random_string(),
                     'recipient_text'    : utils.random_string()},

                    {'conversation'      : conversation_1,
                     'sender_id'         : other_profile_1.global_id,
                     'sender_account'    : other_account_id_1,
                     'recipient_id'      : my_profile.global_id,
                     'recipient_account' : my_account_id,
                     'sender_text'       : utils.random_string(),
                     'recipient_text'    : utils.random_string()},

                    {'conversation'      : conversation_2,
                     'sender_id'         : my_profile.global_id,
                     'sender_account'    : my_account_id,
                     'recipient_id'      : other_profile_2.global_id,
                     'recipient_account' : other_account_id_2,
                     'sender_text'       : utils.random_string(),
                     'recipient_text'    : utils.random_string()},

                    {'conversation'      : conversation_2,
                     'sender_id'         : other_profile_2.global_id,
                     'sender_account'    : other_account_id_2,
                     'recipient_id'      : my_profile.global_id,
                     'recipient_account' : my_account_id,
                     'sender_text'       : utils.random_string(),
                     'recipient_text'    : utils.random_string()}]

        for msg in messages:
            message = Message()
            message.conversation         = msg['conversation']
            message.hash                 = utils.random_string()
            message.timestamp            = timezone.now()
            message.sender_global_id     = msg['sender_id']
            message.recipient_global_id  = msg['recipient_id']
            message.sender_account_id    = msg['sender_account']
            message.recipient_account_id = msg['recipient_account']
            message.sender_text          = msg['sender_text']
            message.recipient_text       = msg['recipient_text']
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

        # Ask the "GET api/messages" endpoint to return the 2 most recent
        # messages.

        url = "/api/messages?my_global_id=%s&num_msgs=2" % my_profile.global_id

        response = self.client.get(url,
                                   "",
                                   content_type="application/json",
                                   **headers)
        if response.status_code == 500:
            print response.content

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], "application/json")
        data = json.loads(response.content)

        # Check that the two most recent messages were correctly returned.

        self.assertItemsEqual(data.keys(), ["messages", "has_more"])
        self.assertEqual(len(data['messages']), 2)
        self.assertEqual(data['has_more'], True)

        for i in range(2):
            orig_msg     = messages[len(messages)-2+i]
            returned_msg = data['messages'][i]

            self.assertEqual(orig_msg['sender_text'],
                             returned_msg['sender_text'])
            self.assertEqual(orig_msg['recipient_text'],
                             returned_msg['recipient_text'])

        # Now ask for the rest of the messages.

        from_msg = data['messages'][0]['hash']

        headers = utils.calc_hmac_headers(
            method="GET",
            url="/api/messages",
            body="",
            account_secret=my_profile.account_secret
        )

        url = "/api/messages?my_global_id=%s&from_msg=%s&num_msgs=-1" \
            % (my_profile.global_id, from_msg)

        response = self.client.get(url,
                                   "",
                                   content_type="application/json",
                                   **headers)
        if response.status_code == 500:
            print response.content

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], "application/json")
        data = json.loads(response.content)

        # Check that the rest of the messages were correctly returned.

        self.assertItemsEqual(data.keys(), ["messages", "has_more"])
        self.assertEqual(len(data['messages']), 2)
        self.assertEqual(data['has_more'], False)

        for i in range(2):
            orig_msg     = messages[i]
            returned_msg = data['messages'][i]

            self.assertEqual(orig_msg['sender_text'],
                             returned_msg['sender_text'])
            self.assertEqual(orig_msg['recipient_text'],
                             returned_msg['recipient_text'])

    # -----------------------------------------------------------------------

    def test_get_conversation_messages(self):
        """ Check that "GET api/messages" returns messages between two users.
        """
        # Create two profiles, for testing.

        sender_profile    = apiTestHelpers.create_profile()
        recipient_profile = apiTestHelpers.create_profile()

        # Create a conversation between these two users.

        conversation = \
            apiTestHelpers.create_conversation(sender_profile.global_id,
                                               recipient_profile.global_id)

        # Create random Ripple account IDs for our two users.

        sender_account_id    = utils.random_string()
        recipient_account_id = utils.random_string()

        # Create some test messages.

        sender_text_1 = utils.random_string()
        sender_text_2 = utils.random_string()
        sender_text_3 = utils.random_string()

        recipient_text_1 = utils.random_string()
        recipient_text_2 = utils.random_string()
        recipient_text_3 = utils.random_string()

        for sender_text,recipient_text in [(sender_text_1, recipient_text_1),
                                           (sender_text_2, recipient_text_2),
                                           (sender_text_3, recipient_text_3)]:
            message = Message()
            message.conversation         = conversation
            message.hash                 = utils.random_string()
            message.timestamp            = timezone.now()
            message.sender_global_id     = sender_profile.global_id
            message.recipient_global_id  = recipient_profile.global_id
            message.sender_account_id    = sender_account_id
            message.recipient_account_id = recipient_account_id
            message.sender_text          = sender_text
            message.recipient_text       = recipient_text
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

        url = "/api/messages?my_global_id=%s&their_global_id=%s&num_msgs=-1" \
            % (sender_profile.global_id, recipient_profile.global_id)

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

        self.assertItemsEqual(data.keys(), ["messages", "has_more"])
        self.assertEqual(len(data['messages']), 3)
        msgs = data['messages']
        self.assertEqual(msgs[0]['sender_text'], sender_text_1)
        self.assertEqual(msgs[1]['sender_text'], sender_text_2)
        self.assertEqual(msgs[2]['sender_text'], sender_text_3)
        self.assertEqual(msgs[0]['recipient_text'], recipient_text_1)
        self.assertEqual(msgs[1]['recipient_text'], recipient_text_2)
        self.assertEqual(msgs[2]['recipient_text'], recipient_text_3)

    # -----------------------------------------------------------------------

    def test_get_messages_finalizes_pending_message(self):
        """ Check that "GET api/messages" finalizes pending messages.

            We create a pending message, and then make a "GET api/messages"
            call, mocking out the Ripple interface to pretend that the message
            was accepted into the Ripple ledger.  We check to ensure that the
            pending message is finalized and appears in the list of final
            messages.
        """
        # Create two profiles, for testing.

        sender_profile    = apiTestHelpers.create_profile()
        recipient_profile = apiTestHelpers.create_profile()

        # Create a conversation between these two users.

        conversation = \
            apiTestHelpers.create_conversation(sender_profile.global_id,
                                               recipient_profile.global_id)

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
        message.sender_text          = utils.random_string()
        message.recipient_text       = utils.random_string()
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

        # Install the mock version of the rippleInterface.request() function.
        # This prevents the rippleInterface module from submitting a message to
        # the Ripple network.

        rippleMock = apiTestHelpers.install_mock_ripple_interface()

        # Ask the "GET api/messages" endpoint to return the messages for this
        # conversation.  All going well, the endpoint should check with the
        # Ripple server, see that the message has been validated, and change
        # the message status to "sent".

        url = "/api/messages?my_global_id=%s&their_global_id=%s&num_msgs=-1" \
            % (sender_profile.global_id, recipient_profile.global_id)

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

