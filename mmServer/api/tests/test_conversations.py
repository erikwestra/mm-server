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

#############################################################################

class ConversationTestCase(django.test.TestCase):
    """ Unit tests for the "Conversation" resource.
    """
    def test_get_conversations(self):
        """ Test the logic for retrieving a list of the user's conversations.
        """
        # Create a bunch of dummy profiles, for testing.

        def create_profile():
            profile = Profile()
            profile.global_id        = utils.calc_unique_global_id()
            profile.account_secret   = utils.random_string()
            profile.name             = utils.random_string()
            profile.name_visible     = True
            profile.location         = utils.random_string()
            profile.location_visible = False
            profile.picture_id       = utils.random_string()
            profile.picture_visible  = True
            profile.save()
            return profile

        my_profile = create_profile()

        other_profiles = []
        for i in range(10):
            other_profile = create_profile()
            other_profiles.append(other_profile)

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

            conversation = Conversation()

            if started_by_me:
                conversation.global_id_1 = my_profile.global_id
                conversation.global_id_2 = other_profile.global_id
                conversation.hidden_1   = hidden_by_me
                conversation.hidden_2   = hidden_by_them
            else:
                conversation.global_id_1 = other_profile.global_id
                conversation.global_id_2 = my_profile.global_id
                conversation.hidden_1    = hidden_by_them
                conversation.hidden_2    = hidden_by_me

            conversation.encryption_key = utils.random_string()
            conversation.last_message   = utils.random_string()
            conversation.last_timestamp = timezone.now()
            conversation.num_unread_1   = 0
            conversation.num_unread_2   = 0

            conversation.save()

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

        their_profile = Profile()
        their_profile.global_id        = utils.calc_unique_global_id()
        their_profile.account_secret   = utils.random_string()
        their_profile.name             = utils.random_string()
        their_profile.name_visible     = True
        their_profile.location         = utils.random_string()
        their_profile.location_visible = False
        their_profile.picture_id       = utils.random_string()
        their_profile.picture_visible  = True
        their_profile.save()

        my_global_id    = my_profile.global_id
        their_global_id = their_profile.global_id

        # Create a conversation between the two users.

        last_message   = utils.random_string()
        last_timestamp = timezone.now()
        encryption_key = utils.random_string()

        conversation = Conversation()
        conversation.global_id_1    = my_global_id
        conversation.global_id_2    = their_global_id
        conversation.encryption_key = encryption_key
        conversation.hidden_1       = True
        conversation.hidden_2       = False
        conversation.last_message   = last_message
        conversation.last_timestamp = last_timestamp
        conversation.num_unread_1   = 1
        conversation.num_unread_2   = 2
        conversation.save()

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

        self.assertEqual(conversation['my_global_id'], my_global_id)
        self.assertEqual(conversation['their_global_id'], their_global_id)
        self.assertEqual(conversation['encryption_key'], encryption_key)
        self.assertEqual(conversation['hidden'], True)
        self.assertEqual(conversation['last_message'], last_message)
        self.assertEqual(conversation['last_timestamp'],
                         utils.datetime_to_unix_timestamp(last_timestamp))
        self.assertEqual(conversation['num_unread'], 1)

    # -----------------------------------------------------------------------

    def test_create_conversation(self):
        """ Test the process of creating a new conversation.
        """
        # Create two profiles for us to use.

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

        their_profile = Profile()
        their_profile.global_id        = utils.calc_unique_global_id()
        their_profile.account_secret   = utils.random_string()
        their_profile.name             = utils.random_string()
        their_profile.name_visible     = True
        their_profile.location         = utils.random_string()
        their_profile.location_visible = False
        their_profile.picture_id       = utils.random_string()
        their_profile.picture_visible  = True
        their_profile.save()

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
        self.assertEqual(conversation.last_message,   None)
        self.assertEqual(conversation.last_timestamp, None)
        self.assertEqual(conversation.num_unread_1,   0)
        self.assertEqual(conversation.num_unread_2,   0)

    # -----------------------------------------------------------------------

    def test_update_conversation(self):
        """ Test the logic of updating a conversation.
        """
        # Create two profiles for us to use.

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

        their_profile = Profile()
        their_profile.global_id        = utils.calc_unique_global_id()
        their_profile.account_secret   = utils.random_string()
        their_profile.name             = utils.random_string()
        their_profile.name_visible     = True
        their_profile.location         = utils.random_string()
        their_profile.location_visible = False
        their_profile.picture_id       = utils.random_string()
        their_profile.picture_visible  = True
        their_profile.save()

        my_global_id    = my_profile.global_id
        their_global_id = their_profile.global_id

        # Create a conversation between the two users.

        last_message   = utils.random_string()
        last_timestamp = timezone.now()

        conversation = Conversation()
        conversation.global_id_1    = my_global_id
        conversation.global_id_2    = their_global_id
        conversation.encryption_key = utils.random_string()
        conversation.hidden_1       = False
        conversation.hidden_2       = False
        conversation.last_message   = last_message
        conversation.last_timestamp = last_timestamp
        conversation.num_unread_1   = 0
        conversation.num_unread_2   = 0
        conversation.save()

        conversation_id = conversation.id

        # The following helper function calls the API to update a conversation.

        def update_conversation(action, **extras):

            request = {'my_global_id'    : my_global_id,
                       'their_global_id' : their_global_id,
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

        # Check the process of adding a message to the conversation.

        new_message = utils.random_string()

        update_conversation("NEW_MESSAGE", message=new_message)

        conversation = Conversation.objects.get(id=conversation.id)

        self.assertEqual(conversation.num_unread_1, 0)
        self.assertEqual(conversation.num_unread_2, 1)
        self.assertEqual(conversation.last_message, new_message)
        self.assertNotEqual(conversation.last_timestamp, last_timestamp)

        # Check the process of marking the conversation as read.

        update_conversation("READ")

        conversation = Conversation.objects.get(id=conversation.id)

        self.assertEqual(conversation.num_unread_1, 0)

        # Check the process of hiding the conversation.

        update_conversation("HIDE")

        conversation = Conversation.objects.get(id=conversation.id)

        self.assertEqual(conversation.hidden_1, True)

        # Check the process of unhiding the conversation.

        update_conversation("UNHIDE")

        conversation = Conversation.objects.get(id=conversation.id)

        self.assertEqual(conversation.hidden_1, False)

