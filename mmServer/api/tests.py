""" mmServer.api.tests

    This module implements the various unit tests for the mmServer.api
    application.
"""
import base64
import logging
import random

from django.utils import unittest, timezone
import django.test

import simplejson as json

from mmServer.shared.models import *
from mmServer.shared.lib    import utils

#############################################################################

class ProfileTestCase(django.test.TestCase):
    """ Unit tests for the "api/profile" endpoint.
    """
    def setUp(self):
        """ Prepare to run our unit tests.

            We disable warnings so that we don't get spurious log messages
            about invalid HMAC authentication while we run our unit tests.
        """
        logging.disable(logging.WARN)


    def tearDown(self):
        """ Clean up after running our unit tests.
        """
        logging.disable(logging.NOTSET)


    def test_get_public_profile(self):
        """ Test the logic of retrieving a user's public profile.
        """
        # Create a dummy profile for testing.

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

        # Ask the "GET api/profile/<GLOBAL_ID>" endpoint to return the
        # publically-visible parts of the profile.

        response = self.client.get("/api/profile/" + profile.global_id)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], "application/json")

        data = json.loads(response.content)

        # Check that only the publically-visible parts of the profile have been
        # returned.

        self.assertIsInstance(data, dict)
        self.assertItemsEqual(data.keys(), ["global_id",
                                            "name",
                                            "picture_id"])

        self.assertEqual(data['global_id'],  profile.global_id)
        self.assertEqual(data['name'],       profile.name)
        self.assertEqual(data['picture_id'], profile.picture_id)

    # -----------------------------------------------------------------------

    def test_get_nonexistent_profile(self):
        """ Check that retrieving a non-existent profile fails.
        """
        global_id = utils.calc_unique_global_id()

        response = self.client.get("/api/profile/" + global_id)

        self.assertEqual(response.status_code, 404)

    # -----------------------------------------------------------------------

    def test_get_own_profile(self):
        """ Test the logic of retrieving a user's own profile.
        """
        # Create a dummy profile for testing.

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

        # Calculate the HMAC authentication headers we need to make an
        # authenticated request.

        headers = utils.calc_hmac_headers(
            method="GET",
            url="/api/profile/"+profile.global_id,
            body="",
            account_secret=profile.account_secret
        )

        # Ask the "GET api/profile/<GLOBAL_ID>" endpoint to return all of the
        # user's profile, using the HMAC authentication headers.

        response = self.client.get("/api/profile/" + profile.global_id,
                                   **headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], "application/json")

        data = json.loads(response.content)

        # Check that the entire profile has been returned.

        self.assertIsInstance(data, dict)
        self.assertItemsEqual(data.keys(), ["global_id",
                                            "name",
                                            "name_visible",
                                            "location",
                                            "location_visible",
                                            "picture_id",
                                            "picture_visible"])

        self.assertEqual(data['global_id'],        profile.global_id)
        self.assertEqual(data['name'],             profile.name)
        self.assertEqual(data['name_visible'],     profile.name_visible)
        self.assertEqual(data['location'],         profile.location)
        self.assertEqual(data['location_visible'], profile.location_visible)
        self.assertEqual(data['picture_id'],       profile.picture_id)
        self.assertEqual(data['picture_visible'],  profile.picture_visible)

    # -----------------------------------------------------------------------

    def test_search_for_profiles(self):
        """ Test the logic for searching for matching profiles.
        """
        # Create 10 dummy profiles, each with a random name starting with the
        # string "match_".  These are the profiles we will search for.

        matching_names = set()
        for i in range(10):
            while True:
                name = "match_" + utils.random_string()
                if name in matching_names:
                    continue
                else:
                    break

            matching_names.add(name)

        for name in matching_names:
            profile = Profile()
            profile.global_id        = utils.calc_unique_global_id()
            profile.account_secret   = utils.random_string()
            profile.name             = name
            profile.name_visible     = True
            profile.location         = utils.random_string()
            profile.location_visible = False
            profile.picture_id       = utils.random_string()
            profile.picture_visible  = True
            profile.save()

        # Create another 20 dummy profiles, each with a random name starting
        # with the string "no_match_".  These are the profiles we don't want
        # included in the search results.

        non_matching_names = set()
        for i in range(20):
            while True: 
                name = "no_match_" + utils.random_string()
                if name in non_matching_names:
                    continue
                else:
                    break

            non_matching_names.add(name)

        for name in non_matching_names:
            profile = Profile()
            profile.global_id        = utils.calc_unique_global_id()
            profile.account_secret   = utils.random_string()
            profile.name             = name
            profile.name_visible     = True
            profile.location         = utils.random_string()
            profile.location_visible = False
            profile.picture_id       = utils.random_string()
            profile.picture_visible  = True
            profile.save()

        # Ask the "GET api/profiles" endpoint to search for profiles starting
        # with the string "match_".

        response = self.client.get("/api/profiles?name=match_")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], "application/json")

        data = json.loads(response.content)

        # Check that the search results include all the matching profiles.

        self.assertItemsEqual(data.keys(), ["success",
                                            "num_pages",
                                            "profiles"])
        self.assertEqual(data['success'], True)

        found_names = set()
        for found_profile in data['profiles']:
            self.assertItemsEqual(found_profile.keys(), ["global_id", "name"])
            profile = Profile.objects.get(global_id=found_profile['global_id'])
            self.assertEqual(profile.name, found_profile['name'])
            found_names.add(found_profile['name'])

        self.assertEqual(found_names, matching_names)

    # -----------------------------------------------------------------------

    def test_invalid_hmac(self):
        """ Check that using an invalid HMAC authentication fails.
        """
        # Create a dummy profile for testing.

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

        # Calculate a different account secret so the HMAC headers will be
        # invalid.

        while True:
            different_account_secret = utils.random_string()
            if profile.account_secret != different_account_secret:
                break

        # Calculate the HMAC authentication headers we need to make an
        # authenticated request.

        headers = utils.calc_hmac_headers(
            method="GET",
            url="/api/profile/"+profile.global_id,
            body="",
            account_secret=different_account_secret
        )

        # Call the "GET api/profile/<GLOBAL_ID>" endpoint with the invalid
        # authentication headers.

        response = self.client.get("/api/profile/" + profile.global_id,
                                   **headers)

        self.assertEqual(response.status_code, 403)

    # -----------------------------------------------------------------------

    def test_create_profile(self):
        """ Test the process of creating a new user profile.
        """
        # Calculate the details of the profile we'll be creating.

        global_id      = utils.calc_unique_global_id()
        account_secret = utils.random_string()

        data = {'global_id'        : global_id,
                'name'             : utils.random_string(),
                'name_visible'     : True,
                'location'         : utils.random_string(),
                'location_visible' : False,
                'picture_id'       : utils.random_string(),
                'picture_visible'  : True}

        # Set up the body of our request.

        request = json.dumps({'account_secret' : account_secret,
                              'profile'        : data})

        # Calculate the HMAC authentication headers we need to make an
        # authenticated request.

        headers = utils.calc_hmac_headers(
            method="POST",
            url="/api/profile/" + global_id,
            body=request,
            account_secret=account_secret
        )

        # Ask the "POST api/profile/<GLOBAL_ID>" endpoint to create the user's
        # profile, using the HMAC authentication headers.

        response = self.client.post("/api/profile/" + global_id,
                                    request,
                                    content_type="application/json",
                                    **headers)

        self.assertEqual(response.status_code, 201)

        # Check that the profile has indeed been created.

        try:
            profile = Profile.objects.get(global_id=global_id)
        except Profile.DoesNotExist:
            profile = None

        self.assertIsNotNone(profile)

        self.assertEqual(profile.global_id,        global_id)
        self.assertEqual(profile.account_secret,   account_secret)
        self.assertEqual(profile.name,             data['name'])
        self.assertEqual(profile.name_visible,     data['name_visible'])
        self.assertEqual(profile.location,         data['location'])
        self.assertEqual(profile.location_visible, data['location_visible'])
        self.assertEqual(profile.picture_id,       data['picture_id'])
        self.assertEqual(profile.picture_visible,  data['picture_visible'])

    # -----------------------------------------------------------------------

    def test_update_profile(self):
        """ Test the process of updating a user profile.
        """
        # Create a dummy profile for testing.

        global_id      = utils.calc_unique_global_id()
        account_secret = utils.random_string()

        profile = Profile()
        profile.global_id        = global_id
        profile.account_secret   = account_secret
        profile.name             = utils.random_string()
        profile.name_visible     = True
        profile.location         = utils.random_string()
        profile.location_visible = False
        profile.picture_id       = utils.random_string()
        profile.picture_visible  = True
        profile.save()

        # Calculate some new data to store into the profile.

        new_name             = utils.random_string()
        new_name_visible     = False
        new_location         = utils.random_string()
        new_location_visible = True
        new_picture_id       = utils.random_string()
        new_picture_visible  = False

        # Set up the body of our request.

        request = json.dumps({'name'             : new_name,
                              'name_visible'     : new_name_visible,
                              'location'         : new_location,
                              'location_visible' : new_location_visible,
                              'picture_id'       : new_picture_id,
                              'picture_visible'  : new_picture_visible})

        # Calculate the HMAC authentication headers we need to make an
        # authenticated request.

        headers = utils.calc_hmac_headers(
            method="PUT",
            url="/api/profile/" + global_id,
            body=request,
            account_secret=account_secret
        )

        # Ask the "PUT api/profile/<GLOBAL_ID>" endpoint to update the user's
        # profile, using the HMAC authentication headers.

        response = self.client.put("/api/profile/" + global_id,
                                   request,
                                   content_type="application/json",
                                   **headers)

        self.assertEqual(response.status_code, 200)

        # Check that the profile has been updated.

        profile = Profile.objects.get(global_id=global_id)

        self.assertEqual(profile.global_id,        global_id)
        self.assertEqual(profile.account_secret,   account_secret)
        self.assertEqual(profile.name,             new_name)
        self.assertEqual(profile.name_visible,     new_name_visible)
        self.assertEqual(profile.location,         new_location)
        self.assertEqual(profile.location_visible, new_location_visible)
        self.assertEqual(profile.picture_id,       new_picture_id)
        self.assertEqual(profile.picture_visible,  new_picture_visible)

    # -----------------------------------------------------------------------

    def test_delete_profile(self):
        """ Test the process of deleting a user profile.
        """
        # Create a dummy profile for testing.

        global_id      = utils.calc_unique_global_id()
        account_secret = utils.random_string()

        profile = Profile()
        profile.global_id        = global_id
        profile.account_secret   = account_secret
        profile.name             = utils.random_string()
        profile.name_visible     = True
        profile.location         = utils.random_string()
        profile.location_visible = False
        profile.picture_id       = utils.random_string()
        profile.picture_visible  = True
        profile.save()

        # Calculate the HMAC authentication headers we need to make an
        # authenticated request.

        headers = utils.calc_hmac_headers(
            method="DELETE",
            url="/api/profile/" + global_id,
            body="",
            account_secret=account_secret
        )

        # Ask the "DELETE api/profile/<GLOBAL_ID>" endpoint to delete the
        # user's profile, using the HMAC authentication headers.

        response = self.client.delete("/api/profile/" + global_id,
                                      **headers)

        self.assertEqual(response.status_code, 200)

        # Check that the profile has been deleted.

        try:
            profile = Profile.objects.get(global_id=global_id)
        except Profile.DoesNotExist:
            profile = None

        self.assertIsNone(profile)

#############################################################################

class PictureTestCase(django.test.TestCase):
    """ Unit tests for the "api/picture" endpoint.
    """
    def test_get_picture(self):
        """ Test the logic of retrieving a picture.
        """
        # Create a dummy picture for testing.

        picture_data = utils.random_string(min_length=10000, max_length=20000)

        picture = Picture()
        picture.picture_id       = utils.calc_unique_picture_id()
        picture.account_secret   = utils.random_string()
        picture.picture_filename = utils.random_string() + ".png"
        picture.picture_data     = base64.b64encode(utils.random_string())
        picture.save()

        # Ask the "GET api/picture/<PICTURE_ID>" endpoint to return the
        # picture.

        response = self.client.get("/api/picture/" + picture.picture_id)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], "image/png")

        # Check that the expected picture data was returned.

        encoded_data = base64.b64encode(response.content)
        self.assertEqual(picture.picture_data, encoded_data)

    # -----------------------------------------------------------------------

    def test_get_nonexistent_picture(self):
        """ Check that retrieving a non-existent picture fails.
        """
        picture_id = utils.calc_unique_picture_id()

        response = self.client.get("/api/picture/" + picture_id)

        self.assertEqual(response.status_code, 404)

    # -----------------------------------------------------------------------

    def test_create_picture(self):
        """ Test the process of uploading a picture.
        """
        account_secret   = utils.random_string()
        picture_filename = utils.random_string()
        picture_data     = utils.random_string(min_length=10000,
                                               max_length=20000)
        encoded_data     = base64.b64encode(picture_data)

        # Set up the body of our request.

        request = json.dumps({'account_secret'   : account_secret,
                              'picture_filename' : picture_filename,
                              'picture_data'     : encoded_data})

        # Calculate the HMAC authentication headers we need to make an
        # authenticated request.

        headers = utils.calc_hmac_headers(
            method="POST",
            url="/api/picture",
            body=request,
            account_secret=account_secret
        )

        # Ask the "POST api/picture" endpoint to upload the picture, using the
        # HMAC authentication headers.

        response = self.client.post("/api/picture",
                                    request,
                                    content_type="application/json",
                                    **headers)

        self.assertEqual(response.status_code, 201)
        picture_id = response.content

        # Check that the picture has been created.

        picture = Picture.objects.get(picture_id=picture_id)

        self.assertEqual(picture.picture_id,       picture_id)
        self.assertEqual(picture.account_secret,   account_secret)
        self.assertEqual(picture.picture_filename, picture_filename)
        self.assertEqual(picture.picture_data,     encoded_data)

    # -----------------------------------------------------------------------

    def test_update_picture(self):
        """ Test the process of updating a picture.
        """
        # Create a dummy picture, for testing.

        picture_data = utils.random_string(min_length=10000, max_length=20000)

        picture = Picture()
        picture.picture_id       = utils.calc_unique_picture_id()
        picture.account_secret   = utils.random_string()
        picture.picture_filename = utils.random_string() + ".png"
        picture.picture_data     = base64.b64encode(utils.random_string())
        picture.save()

        # Calculate the updated picture's details.

        new_picture_filename = utils.random_string()
        new_picture_data     = utils.random_string(min_length=10000,
                                                   max_length=20000)
        new_encoded_data     = base64.b64encode(new_picture_data)

        # Set up the body of our request.

        request = json.dumps({'picture_filename' : new_picture_filename,
                              'picture_data'     : new_encoded_data})

        # Calculate the HMAC authentication headers we need to make an
        # authenticated request.

        headers = utils.calc_hmac_headers(
            method="PUT",
            url="/api/picture/" + picture.picture_id,
            body=request,
            account_secret=picture.account_secret
        )

        # Ask the "PUT api/picture/<PICTURE_ID>" endpoint to update the
        # picture, using the HMAC authentication headers.

        response = self.client.put("/api/picture/" + picture.picture_id,
                                   request,
                                   content_type="application/json",
                                   **headers)

        self.assertEqual(response.status_code, 200)

        # Check that the picture has been created.

        updated_picture = Picture.objects.get(picture_id=picture.picture_id)

        self.assertEqual(updated_picture.picture_filename, new_picture_filename)
        self.assertEqual(updated_picture.picture_data,     new_encoded_data)

    # -----------------------------------------------------------------------

    def test_delete_picture(self):
        """ Test the process of deleting a picture.
        """
        # Create a dummy picture, for testing.

        picture_id   = utils.calc_unique_picture_id()
        picture_data = utils.random_string(min_length=10000, max_length=20000)

        picture = Picture()
        picture.picture_id       = picture_id
        picture.account_secret   = utils.random_string()
        picture.picture_filename = utils.random_string() + ".png"
        picture.picture_data     = base64.b64encode(utils.random_string())
        picture.save()

        # Calculate the HMAC authentication headers we need to make an
        # authenticated request.

        headers = utils.calc_hmac_headers(
            method="DELETE",
            url="/api/picture/" + picture.picture_id,
            body="",
            account_secret=picture.account_secret
        )

        # Ask the "DELETE api/picture/<PICTURE_ID>" endpoint to delete the
        # picture, using the HMAC authentication headers.

        response = self.client.delete("/api/picture/" + picture.picture_id,
                                      **headers)

        self.assertEqual(response.status_code, 200)

        # Check that the picture has been created.

        try:
            picture = Picture.objects.get(picture_id=picture_id)
        except Picture.DoesNotExist:
            picture = None

        self.assertIsNone(picture)

#############################################################################

class ConversationTestCase(django.test.TestCase):
    """ Unit tests for the "api/conversation" endpoint.
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

        conversation = Conversation()
        conversation.global_id_1    = my_global_id
        conversation.global_id_2    = their_global_id
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
                                                    "hidden",
                                                    "last_message",
                                                    "last_timestamp",
                                                    "num_unread"])

        self.assertEqual(conversation['my_global_id'], my_global_id)
        self.assertEqual(conversation['their_global_id'], their_global_id)
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

