""" mmServer.api.tests.test_conversations

    This module implements various unit tests for the "conversation" resource's
    API endpoints.
"""
import random

from django.utils import timezone
import django.test

import simplejson as json

from mmServer.shared.models import *
from mmServer.shared.lib    import utils
from mmServer.api.tests     import apiTestHelpers

#############################################################################

class ConversationTestCase(django.test.TestCase):
    """ Unit tests for the "Conversation" resource.
    """
    def test_get_conversations(self):
        """ Test the logic for retrieving a list of the user's conversations.
        """
        # Create a bunch of dummy profiles, for testing.

        my_profile = apiTestHelpers.create_profile()

        other_profiles = []
        for i in range(10):
            other_profiles.append(apiTestHelpers.create_profile())

        # Now create some conversation records, randomly hiding half of them.
        # Note that, to make the test valid, we randomly set half the
        # conversations to use global_id_1 as the current user, and the other
        # half to use global_id_2 as the current user.  This mimics the effect
        # of having the other user start some of the conversations, and the
        # current user start the rest.

        visible_conversations = set() # global_id of other party.
        hidden_conversations  = set() # global_id of other party.

        for other_profile in other_profiles:
            started_by_me  = random.choice([True, False])
            hidden_by_me   = random.choice([True, False])
            hidden_by_them = random.choice([True, False])

            if started_by_me:
                conversation = \
                    apiTestHelpers.create_conversation(my_profile.global_id,
                                                       other_profile.global_id,
                                                       hidden_by_me,
                                                       hidden_by_them)
            else:
                conversation = \
                    apiTestHelpers.create_conversation(other_profile.global_id,
                                                       my_profile.global_id,
                                                       hidden_by_them,
                                                       hidden_by_me)

            if hidden_by_me:
                hidden_conversations.add(other_profile.global_id)
            else:
                visible_conversations.add(other_profile.global_id)

        # Calculate the HMAC authentication headers we need to make an
        # authenticated request.

        headers = utils.calc_hmac_headers(
            method="GET",
            url="/api/conversations/"+my_profile.global_id,
            body="",
            account_secret=my_profile.account_secret
        )

        # Ask the "GET api/conversations/<GLOBAL_ID>" endpoint to return all of
        # the conversations for this user.

        response = self.client.get("/api/conversations/"+my_profile.global_id,
                                   **headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], "application/json")

        # Check that the API returned the conversations we expected.

        data = json.loads(response.content)
        self.assertItemsEqual(data.keys(), ["conversations"])

        visible_global_ids = set()
        hidden_global_ids  = set()
        for conversation in data['conversations']:
            self.assertItemsEqual(conversation.keys(), ["my_global_id",
                                                        "their_global_id",
                                                        "encryption_key",
                                                        "hidden",
                                                        "last_message",
                                                        "last_timestamp",
                                                        "num_unread"])
            if conversation['hidden']:
                hidden_global_ids.add(conversation['their_global_id'])
            else:
                visible_global_ids.add(conversation['their_global_id'])

        self.assertEqual(visible_conversations, visible_global_ids)
        self.assertEqual(hidden_conversations, hidden_global_ids)

    # -----------------------------------------------------------------------

    def test_get_conversation(self):
        """ Test the logic for retrieving a single conversation.
        """
        # Create two profiles for us to use.

        my_profile    = apiTestHelpers.create_profile()
        their_profile = apiTestHelpers.create_profile()

        my_global_id    = my_profile.global_id
        their_global_id = their_profile.global_id

        # Create a conversation between the two users.

        conversation = apiTestHelpers.create_conversation(my_global_id,
                                                          their_global_id,
                                                          hidden_1=True,
                                                          num_unread_1=2)

        encryption_key = conversation.encryption_key
        last_message   = conversation.last_message_1
        last_timestamp = conversation.last_timestamp
        last_secs      = utils.datetime_to_unix_timestamp(last_timestamp)

        # Calculate the HMAC authentication headers we need to make an
        # authenticated request.

        headers = utils.calc_hmac_headers(
            method="GET",
            url="/api/conversation",
            body="",
            account_secret=my_profile.account_secret
        )

        # Ask the "GET /api/conversation' endpoint to return the details of our
        # conversation.

        response = self.client.get("/api/conversation" +
                                   "?my_global_id=" + my_global_id +
                                   "&their_global_id=" + their_global_id,
                                   **headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], "application/json")

        # Check that the conversation's details were correctly returned.

        data = json.loads(response.content)
        self.assertItemsEqual(data.keys(), ["conversation"])
        conversation = data['conversation']

        self.assertItemsEqual(conversation.keys(), ["my_global_id",
                                                    "their_global_id",
                                                    "encryption_key",
                                                    "hidden",
                                                    "last_message",
                                                    "last_timestamp",
                                                    "num_unread"])

        self.assertEqual(conversation['my_global_id'],    my_global_id)
        self.assertEqual(conversation['their_global_id'], their_global_id)
        self.assertEqual(conversation['encryption_key'],  encryption_key)
        self.assertEqual(conversation['hidden'],          True)
        self.assertEqual(conversation['last_message'],    last_message)
        self.assertEqual(conversation['last_timestamp'],  last_secs)
        self.assertEqual(conversation['num_unread'],      2)

    # -----------------------------------------------------------------------

    def test_create_conversation(self):
        """ Test the process of creating a new conversation.
        """
        # Create two profiles for us to use.

        my_profile    = apiTestHelpers.create_profile()
        their_profile = apiTestHelpers.create_profile()

        my_global_id    = my_profile.global_id
        their_global_id = their_profile.global_id

        # Create the body of our request.

        request = json.dumps({'my_global_id'    : my_global_id,
                              'their_global_id' : their_global_id})

        # Calculate the HMAC authentication headers we need to make an
        # authenticated request.

        headers = utils.calc_hmac_headers(
            method="POST",
            url="/api/conversation",
            body=request,
            account_secret=my_profile.account_secret
        )

        # Ask the "POST api/conversation" endpoint to create a new
        # conversation between these two users.

        response = self.client.post("/api/conversation",
                                    request,
                                    content_type="application/json",
                                    **headers)
        self.assertEqual(response.status_code, 201)

        # Check that the conversation was indeed created.

        try:
            conversation = Conversation.objects.get(
                                    global_id_1=my_global_id,
                                    global_id_2=their_global_id)
        except Conversation.DoesNotExist:
            conversation = Conversation.objects.get(
                                    global_id_1=their_global_id,
                                    global_id_2=my_global_id)

        self.assertNotIn(conversation.encryption_key, [None, ""])
        self.assertEqual(conversation.hidden_1,       False)
        self.assertEqual(conversation.hidden_2,       False)
        self.assertEqual(conversation.last_message_1, None)
        self.assertEqual(conversation.last_message_2, None)
        self.assertEqual(conversation.last_timestamp, None)
        self.assertEqual(conversation.num_unread_1,   0)
        self.assertEqual(conversation.num_unread_2,   0)

    # -----------------------------------------------------------------------

    def test_update_conversation(self):
        """ Test the logic of updating a conversation.
        """
        # Create two profiles for us to use.

        my_profile    = apiTestHelpers.create_profile()
        their_profile = apiTestHelpers.create_profile()

        # Create a conversation between the two users.

        conversation = \
            apiTestHelpers.create_conversation(my_profile.global_id,
                                               their_profile.global_id)

        # The following helper function calls the API to update a conversation.

        def update_conversation(action, **extras):

            request = {'my_global_id'    : my_profile.global_id,
                       'their_global_id' : their_profile.global_id,
                       'action'          : action}
            request.update(extras)
            request = json.dumps(request)

            headers = utils.calc_hmac_headers(
                method="PUT",
                url="/api/conversation",
                body=request,
                account_secret=my_profile.account_secret
            )

            response = self.client.put("/api/conversation",
                                       request,
                                       content_type="application/json",
                                       **headers)
            self.assertEqual(response.status_code, 200)

        # Check the process of hiding the conversation.

        update_conversation("HIDE")

        conversation = Conversation.objects.get(id=conversation.id)

        self.assertEqual(conversation.hidden_1, True)

        # Check the process of unhiding the conversation.

        update_conversation("UNHIDE")

        conversation = Conversation.objects.get(id=conversation.id)

        self.assertEqual(conversation.hidden_1, False)

    # -----------------------------------------------------------------------

    def test_sent_message_updates_conversation(self):
        """ Check that a message with status="sent" updates the conversation.

            We create a pending message, and then make a "GET api/messages"
            call, mocking out the Ripple interface to pretend that the message
            was accepted into the Ripple ledger.  This will change the
            message's status to "SENT", and should update the conversation with
            the details of the newly-sent message.
        """
        # Create two profiles for us to use.

        my_profile    = apiTestHelpers.create_profile()
        their_profile = apiTestHelpers.create_profile()

        my_global_id    = my_profile.global_id
        their_global_id = their_profile.global_id

        # Create a conversation between the two users.

        conversation = \
            apiTestHelpers.create_conversation(my_profile.global_id,
                                               their_profile.global_id)

        cur_last_message_1 = conversation.last_message_1
        cur_last_message_2 = conversation.last_message_2
        cur_last_timestamp = conversation.last_timestamp
        cur_num_unread_1   = conversation.num_unread_1
        cur_num_unread_2   = conversation.num_unread_2

        # Create two random Ripple account IDs.

        my_account_id    = utils.random_string()
        their_account_id = utils.random_string()

        # Create a dummy pending message.

        message = Message()
        message.conversation         = conversation
        message.hash                 = utils.random_string()
        message.timestamp            = timezone.now()
        message.sender_global_id     = my_profile.global_id
        message.recipient_global_id  = their_profile.global_id
        message.sender_account_id    = my_account_id
        message.recipient_account_id = their_account_id
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
            account_secret=my_profile.account_secret
        )

        # Install the mock version of the rippleInterface.request() function.
        # This prevents the rippleInterface module from submitting a message to
        # the Ripple network.

        rippleMock = apiTestHelpers.install_mock_ripple_interface()

        # Ask the "GET /api/messages" endpoint to return the messages for this
        # conversation.  All going well, the endpoint should check with the
        # Ripple server, see that the message was validated, change the
        # message status to "sent" and update the conversation to match.

        url = "/api/messages?my_global_id=" + my_profile.global_id \
            + "&their_global_id=" + their_profile.global_id

        response = self.client.get(url, **headers)
        self.assertEqual(response.status_code, 200)

        # Check that the conversation has been updated.

        conversation = Conversation.objects.get(id=conversation.id)

        self.assertNotEqual(conversation.last_timestamp, cur_last_timestamp)
        self.assertEqual(conversation.last_message_1, message.sender_text)
        self.assertEqual(conversation.num_unread_1, cur_num_unread_1)
        self.assertEqual(conversation.num_unread_2, cur_num_unread_2 + 1)

    # -----------------------------------------------------------------------

    def test_read_message_updates_conversation(self):
        """ Check that marking a message as "read" updates the conversation.

            We create a sent message, and then make a "PUT api/message" call to
            mark the message as read.  This should update the conversation to
            reflect the fact the message was sent.
        """
        # Create two profiles for us to use.

        my_profile    = apiTestHelpers.create_profile()
        their_profile = apiTestHelpers.create_profile()

        my_global_id    = my_profile.global_id
        their_global_id = their_profile.global_id

        # Create a conversation between the two users.

        conversation = \
            apiTestHelpers.create_conversation(my_profile.global_id,
                                               their_profile.global_id,
                                               num_unread_1=0,
                                               num_unread_2=1)

        cur_last_message_1 = conversation.last_message_1
        cur_last_message_2 = conversation.last_message_2
        cur_last_timestamp = conversation.last_timestamp
        cur_num_unread_1   = conversation.num_unread_1
        cur_num_unread_2   = conversation.num_unread_2

        # Create two random Ripple account IDs.

        my_account_id    = utils.random_string()
        their_account_id = utils.random_string()

        # Create a dummy sent message.

        message = Message()
        message.conversation         = conversation
        message.hash                 = utils.random_string()
        message.timestamp            = timezone.now()
        message.sender_global_id     = my_profile.global_id
        message.recipient_global_id  = their_profile.global_id
        message.sender_account_id    = my_account_id
        message.recipient_account_id = their_account_id
        message.sender_text          = utils.random_string()
        message.recipient_text       = utils.random_string()
        message.status               = Message.STATUS_SENT
        message.error                = None
        message.save()

        # Prepare the body of our request.

        request = json.dumps({'message' : {'hash' : message.hash,
                                           'read' : True}})

        # Calculate the HMAC authentication headers we need to make an
        # authenticated request.

        headers = utils.calc_hmac_headers(
            method="PUT",
            url="/api/message",
            body=request,
            account_secret=their_profile.account_secret
        )

        # Ask the "PUT /api/message" endpoint to mark the message as read.  All
        # going well, the endpoint should update the conversation to reflect
        # this change.

        response = self.client.put("/api/message",
                                   request,
                                   content_type="application/json",
                                   **headers)
        self.assertEqual(response.status_code, 200)

        # Check that the conversation has been updated.

        conversation = Conversation.objects.get(id=conversation.id)

        self.assertNotEqual(conversation.last_timestamp, cur_last_timestamp)
        self.assertEqual(conversation.last_message_1, message.sender_text)
        self.assertEqual(conversation.last_message_2, message.recipient_text)
        self.assertEqual(conversation.num_unread_1, cur_num_unread_1)
        self.assertEqual(conversation.num_unread_2, cur_num_unread_2 - 1)

