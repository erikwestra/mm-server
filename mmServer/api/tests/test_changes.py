""" mmServer.api.tests.test_changes

    This module implements various unit tests for the "changes" API endpoint.
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

class ChangesTestCase(django.test.TestCase):
    """ Unit tests for the "changes" endpoint.
    """
    def test_add_profile(self):
        """ Test that the "/changes" endpoint detects a newly-added profile.
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

        # Calculate a global ID and account secret for the other user.  Note
        # that the user won't have a profile yet.

        other_user_global_id      = utils.calc_unique_global_id()
        other_user_account_secret = utils.random_string()

        # Create a conversation between these two users.

        conversation = Conversation()
        conversation.global_id_1    = my_profile.global_id
        conversation.global_id_2    = other_user_global_id
        conversation.hidden_1       = False
        conversation.hidden_2       = False
        conversation.encryption_key = encryption.generate_random_key()
        conversation.last_message   = utils.random_string()
        conversation.last_timestamp = timezone.now()
        conversation.num_unread_1   = 0
        conversation.num_unread_2   = 0
        conversation.save()

        # Ask the "/changes" endpoint for the current anchor value.

        headers = utils.calc_hmac_headers(
            method="GET",
            url="/api/changes",
            body="",
            account_secret=my_profile.account_secret
        )

        url = "/api/changes?my_global_id=" + my_profile.global_id
        response = self.client.get(url, "", content_type="application/json",
                                   **headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], "application/json")
        data = json.loads(response.content)
        self.assertItemsEqual(data.keys(), ["next_anchor"])

        anchor = data['next_anchor']

        # Create a new profile for the second user.

        request = json.dumps({
            'profile' : {
                'global_id'        : other_user_global_id,
                'name'             : utils.random_string(),
                'name_visible'     : True,
                'location'         : utils.random_string(),
                'location_visible' : True,
                'picture_id'       : utils.random_string(),
                'picture_visible'  : True,
            },
            'account_secret' : other_user_account_secret,
        })

        headers = utils.calc_hmac_headers(
            method="POST",
            url="/api/profile/" + other_user_global_id,
            body=request,
            account_secret=other_user_account_secret
        )

        response = self.client.post("/api/profile/" + other_user_global_id,
                                    request,
                                    content_type="application/json",
                                    **headers)

        self.assertEqual(response.status_code, 201)

        # Now ask the "/changes" endpoint for the things that have changed
        # since the anchor was calculated.

        headers = utils.calc_hmac_headers(
            method="GET",
            url="/api/changes",
            body="",
            account_secret=my_profile.account_secret
        )

        url = "/api/changes?my_global_id=" + my_profile.global_id \
                              + "&anchor=" + anchor

        response = self.client.get(url, "", content_type="application/json",
                                   **headers)
        if response.status_code != 200:
            print response.content
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], "application/json")
        data = json.loads(response.content)
        self.assertItemsEqual(data.keys(), ["changes", "next_anchor"])

        # Check that the changes includes the updated profile.

        found = False
        for change in data['changes']:
            if change['type'] == "profile":
                if change['data']['global_id'] == other_user_global_id:
                    found = True

        self.assertTrue(found)

    # =======================================================================

    def test_update_profile(self):
        """ Test that the "/changes" endpoint detects an updated profile.
        """
        # Create profiles for two users.

        profile_1 = Profile()
        profile_1.global_id        = utils.calc_unique_global_id()
        profile_1.account_secret   = utils.random_string()
        profile_1.name             = utils.random_string()
        profile_1.name_visible     = True
        profile_1.location         = utils.random_string()
        profile_1.location_visible = False
        profile_1.picture_id       = utils.random_string()
        profile_1.picture_visible  = True
        profile_1.save()

        profile_2 = Profile()
        profile_2.global_id        = utils.calc_unique_global_id()
        profile_2.account_secret   = utils.random_string()
        profile_2.name             = utils.random_string()
        profile_2.name_visible     = True
        profile_2.location         = utils.random_string()
        profile_2.location_visible = False
        profile_2.picture_id       = utils.random_string()
        profile_2.picture_visible  = True
        profile_2.save()

        # Create a conversation between these two users.

        conversation = Conversation()
        conversation.global_id_1    = profile_1.global_id
        conversation.global_id_2    = profile_2.global_id
        conversation.hidden_1       = False
        conversation.hidden_2       = False
        conversation.encryption_key = encryption.generate_random_key()
        conversation.last_message   = utils.random_string()
        conversation.last_timestamp = timezone.now()
        conversation.num_unread_1   = 0
        conversation.num_unread_2   = 0
        conversation.save()

        # Ask the "/changes" endpoint for the current anchor value.

        headers = utils.calc_hmac_headers(
            method="GET",
            url="/api/changes",
            body="",
            account_secret=profile_1.account_secret
        )

        url = "/api/changes?my_global_id=" + profile_1.global_id
        response = self.client.get(url, "", content_type="application/json",
                                   **headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], "application/json")
        data = json.loads(response.content)
        self.assertItemsEqual(data.keys(), ["next_anchor"])

        anchor = data['next_anchor']

        # Calculate some new data to store into the second profile.

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
            url="/api/profile/" + profile_2.global_id,
            body=request,
            account_secret=profile_2.account_secret
        )

        # Ask the "PUT api/profile/<GLOBAL_ID>" endpoint to update the user's
        # profile.

        response = self.client.put("/api/profile/" + profile_2.global_id,
                                   request,
                                   content_type="application/json",
                                   **headers)

        self.assertEqual(response.status_code, 200)

        # Now ask the "/changes" endpoint for the things that have changed
        # since the anchor was calculated.

        headers = utils.calc_hmac_headers(
            method="GET",
            url="/api/changes",
            body="",
            account_secret=profile_1.account_secret
        )

        url = "/api/changes?my_global_id=" + profile_1.global_id \
                              + "&anchor=" + anchor

        response = self.client.get(url, "", content_type="application/json",
                                   **headers)
        if response.status_code != 200:
            print response.content
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], "application/json")
        data = json.loads(response.content)
        self.assertItemsEqual(data.keys(), ["changes", "next_anchor"])

        # Check that the changes includes the updated profile.

        found = False
        for change in data['changes']:
            if change['type'] == "profile":
                if change['data']['global_id'] == profile_2.global_id:
                    found = True

        self.assertTrue(found)

    # =======================================================================

    def test_delete_profile(self):
        """ Test that the "/changes" endpoint detects a deleted profile.
        """
        # Create profiles for two users.

        profile_1 = Profile()
        profile_1.global_id        = utils.calc_unique_global_id()
        profile_1.account_secret   = utils.random_string()
        profile_1.name             = utils.random_string()
        profile_1.name_visible     = True
        profile_1.location         = utils.random_string()
        profile_1.location_visible = False
        profile_1.picture_id       = utils.random_string()
        profile_1.picture_visible  = True
        profile_1.save()

        profile_2 = Profile()
        profile_2.global_id        = utils.calc_unique_global_id()
        profile_2.account_secret   = utils.random_string()
        profile_2.name             = utils.random_string()
        profile_2.name_visible     = True
        profile_2.location         = utils.random_string()
        profile_2.location_visible = False
        profile_2.picture_id       = utils.random_string()
        profile_2.picture_visible  = True
        profile_2.save()

        # Create a conversation between these two users.

        conversation = Conversation()
        conversation.global_id_1    = profile_1.global_id
        conversation.global_id_2    = profile_2.global_id
        conversation.hidden_1       = False
        conversation.hidden_2       = False
        conversation.encryption_key = encryption.generate_random_key()
        conversation.last_message   = utils.random_string()
        conversation.last_timestamp = timezone.now()
        conversation.num_unread_1   = 0
        conversation.num_unread_2   = 0
        conversation.save()

        # Ask the "/changes" endpoint for the current anchor value.

        headers = utils.calc_hmac_headers(
            method="GET",
            url="/api/changes",
            body="",
            account_secret=profile_1.account_secret
        )

        url = "/api/changes?my_global_id=" + profile_1.global_id
        response = self.client.get(url, "", content_type="application/json",
                                   **headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], "application/json")
        data = json.loads(response.content)
        self.assertItemsEqual(data.keys(), ["next_anchor"])

        anchor = data['next_anchor']

        # Ask the API to delete the second profile.

        headers = utils.calc_hmac_headers(
            method="DELETE",
            url="/api/profile/" + profile_2.global_id,
            body="",
            account_secret=profile_2.account_secret
        )

        response = self.client.delete("/api/profile/" + profile_2.global_id,
                                      **headers)

        self.assertEqual(response.status_code, 200)

        # Now ask the "/changes" endpoint for the things that have changed
        # since the anchor was calculated.

        headers = utils.calc_hmac_headers(
            method="GET",
            url="/api/changes",
            body="",
            account_secret=profile_1.account_secret
        )

        url = "/api/changes?my_global_id=" + profile_1.global_id \
                              + "&anchor=" + anchor

        response = self.client.get(url,
                                   **headers)
        if response.status_code != 200:
            print response.content
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], "application/json")
        data = json.loads(response.content)
        self.assertItemsEqual(data.keys(), ["changes", "next_anchor"])

        # Check that the changes includes the deleted profile.

        found = False
        for change in data['changes']:
            if change['type'] == "profile":
                if change['data']['global_id'] == profile_2.global_id:
                    if change['data'].get("deleted"):
                        found = True

        self.assertTrue(found)

    # =======================================================================

    def test_add_picture(self):
        """ Test that the "/changes" endpoint detects a newly-added picture.
        """
        # Create a dummy profile.

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

        # Ask the "/changes" endpoint for the current anchor value.

        headers = utils.calc_hmac_headers(
            method="GET",
            url="/api/changes",
            body="",
            account_secret=profile.account_secret
        )

        url = "/api/changes?my_global_id=" + profile.global_id
        response = self.client.get(url, "", content_type="application/json",
                                   **headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], "application/json")
        data = json.loads(response.content)
        self.assertItemsEqual(data.keys(), ["next_anchor"])

        anchor = data['next_anchor']

        # Ask the API to create a new picture.

        account_secret   = utils.random_string()
        picture_filename = utils.random_string()
        picture_data     = utils.random_string(min_length=10000,
                                               max_length=20000)
        encoded_data     = base64.b64encode(picture_data)

        request = json.dumps({'account_secret'   : account_secret,
                              'picture_filename' : picture_filename,
                              'picture_data'     : encoded_data})

        headers = utils.calc_hmac_headers(
            method="POST",
            url="/api/picture",
            body=request,
            account_secret=account_secret
        )

        response = self.client.post("/api/picture",
                                    request,
                                    content_type="application/json",
                                    **headers)

        self.assertEqual(response.status_code, 201)
        picture_id = response.content

        # Now ask the "/changes" endpoint for the things that have changed
        # since the anchor was calculated.

        headers = utils.calc_hmac_headers(
            method="GET",
            url="/api/changes",
            body="",
            account_secret=profile.account_secret
        )

        url = "/api/changes?my_global_id=" + profile.global_id \
                              + "&anchor=" + anchor

        response = self.client.get(url,
                                   **headers)
        if response.status_code != 200:
            print response.content
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], "application/json")
        data = json.loads(response.content)
        self.assertItemsEqual(data.keys(), ["changes", "next_anchor"])

        # Check that the changes includes the newly-created picture.

        found = False 
        for change in data['changes']:
            if change['type'] == "picture":
                if change['data']['picture_id'] == picture_id:
                    found = True
                    break

        self.assertTrue(found)

    # =======================================================================

    def test_update_picture(self):
        """ Test that the "/changes" endpoint detects an updated picture.
        """
        # Create a dummy profile.

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

        # Create a dummy picture.

        picture = Picture()
        picture.picture_id       = utils.calc_unique_picture_id()
        picture.deleted          = False
        picture.account_secret   = utils.random_string()
        picture.picture_filename = utils.random_string() + ".png"
        picture.picture_data     = base64.b64encode(utils.random_string())
        picture.save()

        # Ask the "/changes" endpoint for the current anchor value.

        headers = utils.calc_hmac_headers(
            method="GET",
            url="/api/changes",
            body="",
            account_secret=profile.account_secret
        )

        url = "/api/changes?my_global_id=" + profile.global_id
        response = self.client.get(url, "", content_type="application/json",
                                   **headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], "application/json")
        data = json.loads(response.content)
        self.assertItemsEqual(data.keys(), ["next_anchor"])

        anchor = data['next_anchor']

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

        # Now ask the "/changes" endpoint for the things that have changed
        # since the anchor was calculated.

        headers = utils.calc_hmac_headers(
            method="GET",
            url="/api/changes",
            body="",
            account_secret=profile.account_secret
        )

        url = "/api/changes?my_global_id=" + profile.global_id \
                              + "&anchor=" + anchor

        response = self.client.get(url,
                                   **headers)
        if response.status_code != 200:
            print response.content
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], "application/json")
        data = json.loads(response.content)
        self.assertItemsEqual(data.keys(), ["changes", "next_anchor"])

        # Check that the changes includes the updated picture.

        found = False 
        for change in data['changes']:
            if change['type'] == "picture":
                if change['data']['picture_id'] == picture.picture_id:
                    found = True
                    break

        self.assertTrue(found)

    # =======================================================================

    def test_delete_picture(self):
        """ Test that the "/changes" endpoint detects a deleted picture.
        """
        # Create a dummy profile.

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

        # Create a dummy picture.

        picture = Picture()
        picture.picture_id       = utils.calc_unique_picture_id()
        picture.deleted          = False
        picture.account_secret   = utils.random_string()
        picture.picture_filename = utils.random_string() + ".png"
        picture.picture_data     = base64.b64encode(utils.random_string())
        picture.save()

        # Ask the "/changes" endpoint for the current anchor value.

        headers = utils.calc_hmac_headers(
            method="GET",
            url="/api/changes",
            body="",
            account_secret=profile.account_secret
        )

        url = "/api/changes?my_global_id=" + profile.global_id
        response = self.client.get(url, "", content_type="application/json",
                                   **headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], "application/json")
        data = json.loads(response.content)
        self.assertItemsEqual(data.keys(), ["next_anchor"])

        anchor = data['next_anchor']

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

        # Now ask the "/changes" endpoint for the things that have changed
        # since the anchor was calculated.

        headers = utils.calc_hmac_headers(
            method="GET",
            url="/api/changes",
            body="",
            account_secret=profile.account_secret
        )

        url = "/api/changes?my_global_id=" + profile.global_id \
                              + "&anchor=" + anchor

        response = self.client.get(url,
                                   **headers)
        if response.status_code != 200:
            print response.content
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], "application/json")
        data = json.loads(response.content)
        self.assertItemsEqual(data.keys(), ["changes", "next_anchor"])

        # Check that the changes includes the deleted picture.

        found   = False
        deleted = False
        for change in data['changes']:
            if change['type'] == "picture":
                if change['data']['picture_id'] == picture.picture_id:
                    found   = True
                    deleted = change['data'].get("deleted")
                    break

        self.assertTrue(found)
        self.assertTrue(deleted)

    # =======================================================================

    def test_add_conversation(self):
        """ Test that the "/changes" endpoint detects an added conversation.
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

        # Ask the "/changes" endpoint for the current anchor value.

        headers = utils.calc_hmac_headers(
            method="GET",
            url="/api/changes",
            body="",
            account_secret=my_profile.account_secret
        )

        url = "/api/changes?my_global_id=" + my_profile.global_id
        response = self.client.get(url, "", content_type="application/json",
                                   **headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], "application/json")
        data = json.loads(response.content)
        self.assertItemsEqual(data.keys(), ["next_anchor"])

        anchor = data['next_anchor']

        # Ask the API to create a new conversation.

        request = json.dumps({'my_global_id'    : my_global_id,
                              'their_global_id' : their_global_id})

        headers = utils.calc_hmac_headers(
            method="POST",
            url="/api/conversation",
            body=request,
            account_secret=my_profile.account_secret
        )

        response = self.client.post("/api/conversation",
                                    request,
                                    content_type="application/json",
                                    **headers)
        self.assertEqual(response.status_code, 201)

        # Now ask the "/changes" endpoint for the things that have changed
        # since the anchor was calculated.

        headers = utils.calc_hmac_headers(
            method="GET",
            url="/api/changes",
            body="",
            account_secret=my_profile.account_secret
        )

        url = "/api/changes?my_global_id=" + my_profile.global_id \
                              + "&anchor=" + anchor

        response = self.client.get(url,
                                   **headers)
        if response.status_code != 200:
            print response.content
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], "application/json")
        data = json.loads(response.content)
        self.assertItemsEqual(data.keys(), ["changes", "next_anchor"])

        # Check that the changes includes the new conversation.

        found = False
        for change in data['changes']:
            if change['type'] == "conversation":
                if (change['data']['my_global_id'] == my_global_id and
                    change['data']['their_global_id'] == their_global_id):
                    found = True

        self.assertTrue(found)

    # =======================================================================

    def test_update_conversation(self):
        """ Test that the "/changes" endpoint detects an updated conversation.
        """
        # Create profiles for two users.

        profile_1 = Profile()
        profile_1.global_id        = utils.calc_unique_global_id()
        profile_1.account_secret   = utils.random_string()
        profile_1.name             = utils.random_string()
        profile_1.name_visible     = True
        profile_1.location         = utils.random_string()
        profile_1.location_visible = False
        profile_1.picture_id       = utils.random_string()
        profile_1.picture_visible  = True
        profile_1.save()

        profile_2 = Profile()
        profile_2.global_id        = utils.calc_unique_global_id()
        profile_2.account_secret   = utils.random_string()
        profile_2.name             = utils.random_string()
        profile_2.name_visible     = True
        profile_2.location         = utils.random_string()
        profile_2.location_visible = False
        profile_2.picture_id       = utils.random_string()
        profile_2.picture_visible  = True
        profile_2.save()

        # Create a conversation between these two users.

        conversation = Conversation()
        conversation.global_id_1    = profile_1.global_id
        conversation.global_id_2    = profile_2.global_id
        conversation.hidden_1       = False
        conversation.hidden_2       = False
        conversation.encryption_key = encryption.generate_random_key()
        conversation.last_message   = utils.random_string()
        conversation.last_timestamp = timezone.now()
        conversation.num_unread_1   = 0
        conversation.num_unread_2   = 0
        conversation.save()

        # Ask the "/changes" endpoint for the current anchor value.

        headers = utils.calc_hmac_headers(
            method="GET",
            url="/api/changes",
            body="",
            account_secret=profile_1.account_secret
        )

        url = "/api/changes?my_global_id=" + profile_1.global_id
        response = self.client.get(url, "", content_type="application/json",
                                   **headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], "application/json")
        data = json.loads(response.content)
        self.assertItemsEqual(data.keys(), ["next_anchor"])

        anchor = data['next_anchor']

        # Ask the API to update the conversation.

        request = json.dumps({'my_global_id'    : profile_1.global_id,
                              'their_global_id' : profile_2.global_id,
                              'action'          : "NEW_MESSAGE",
                              'message'         : utils.random_string()})

        headers = utils.calc_hmac_headers(
            method="PUT",
            url="/api/conversation",
            body=request,
            account_secret=profile_1.account_secret
        )

        response = self.client.put("/api/conversation",
                                   request,
                                   content_type="application/json",
                                   **headers)
        self.assertEqual(response.status_code, 200)

        # Now ask the "/changes" endpoint for the things that have changed
        # since the anchor was calculated.

        headers = utils.calc_hmac_headers(
            method="GET",
            url="/api/changes",
            body="",
            account_secret=profile_1.account_secret
        )

        url = "/api/changes?my_global_id=" + profile_1.global_id \
                              + "&anchor=" + anchor

        response = self.client.get(url,
                                   **headers)
        if response.status_code != 200:
            print response.content
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], "application/json")
        data = json.loads(response.content)
        self.assertItemsEqual(data.keys(), ["changes", "next_anchor"])

        # Check that the changes includes the updated conversation.

        found = False
        for change in data['changes']:
            if change['type'] == "conversation":
                if (change['data']['my_global_id'] == profile_1.global_id and
                    change['data']['their_global_id'] == profile_2.global_id):
                    found = True

        self.assertTrue(found)

    # =======================================================================

    def test_add_message(self):
        """ Test that the "/changes" endpoint detects a new message.
        """
        # Create profiles for two users.

        profile_1 = Profile()
        profile_1.global_id        = utils.calc_unique_global_id()
        profile_1.account_secret   = utils.random_string()
        profile_1.name             = utils.random_string()
        profile_1.name_visible     = True
        profile_1.location         = utils.random_string()
        profile_1.location_visible = False
        profile_1.picture_id       = utils.random_string()
        profile_1.picture_visible  = True
        profile_1.save()

        profile_2 = Profile()
        profile_2.global_id        = utils.calc_unique_global_id()
        profile_2.account_secret   = utils.random_string()
        profile_2.name             = utils.random_string()
        profile_2.name_visible     = True
        profile_2.location         = utils.random_string()
        profile_2.location_visible = False
        profile_2.picture_id       = utils.random_string()
        profile_2.picture_visible  = True
        profile_2.save()

        # Create a conversation between these two users.

        conversation = Conversation()
        conversation.global_id_1    = profile_1.global_id
        conversation.global_id_2    = profile_2.global_id
        conversation.hidden_1       = False
        conversation.hidden_2       = False
        conversation.encryption_key = encryption.generate_random_key()
        conversation.last_message   = utils.random_string()
        conversation.last_timestamp = timezone.now()
        conversation.num_unread_1   = 0
        conversation.num_unread_2   = 0
        conversation.save()

        # Create two random Ripple account IDs.

        sender_account_id    = utils.random_string()
        recipient_account_id = utils.random_string()

        # Ask the "/changes" endpoint for the current anchor value.

        headers = utils.calc_hmac_headers(
            method="GET",
            url="/api/changes",
            body="",
            account_secret=profile_1.account_secret
        )

        url = "/api/changes?my_global_id=" + profile_1.global_id
        response = self.client.get(url, "", content_type="application/json",
                                   **headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], "application/json")
        data = json.loads(response.content)
        self.assertItemsEqual(data.keys(), ["next_anchor"])

        anchor = data['next_anchor']

        # Create the body of our request.

        message_text = utils.random_string()

        request = json.dumps(
                        {'sender_global_id'     : profile_1.global_id,
                         'recipient_global_id'  : profile_2.global_id,
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
            account_secret=profile_1.account_secret
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
        if response.status_code != 202:
            print response.content
        self.assertEqual(response.status_code, 202)

        # Setup another mock version of the rippleInterface.request() function.
        # This one replaces the call to rippleInterface.request() in our view
        # function so the API doesn't actually ask the Ripple network for the
        # status of the message when we poll for updates.

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

        # Now ask the "/changes" endpoint for the things that have changed
        # since the anchor was calculated.

        headers = utils.calc_hmac_headers(
            method="GET",
            url="/api/changes",
            body="",
            account_secret=profile_1.account_secret
        )

        url = "/api/changes?my_global_id=" + profile_1.global_id \
                              + "&anchor=" + anchor

        response = self.client.get(url,
                                   **headers)
        if response.status_code != 200:
            print response.content
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], "application/json")
        data = json.loads(response.content)
        self.assertItemsEqual(data.keys(), ["changes", "next_anchor"])

        # Check that the changes includes the new message.

        found = False
        for change in data['changes']:
            if change['type'] == "message":
                msg = change['data']
                if (msg['sender_global_id'] == profile_1.global_id and
                    msg['recipient_global_id'] == profile_2.global_id):
                    found = True

        self.assertTrue(found)

    # =======================================================================

    def test_update_message(self):
        """ Test that the "/changes" endpoint detects an updated message.
        """
        # Create profiles for two users.

        profile_1 = Profile()
        profile_1.global_id        = utils.calc_unique_global_id()
        profile_1.account_secret   = utils.random_string()
        profile_1.name             = utils.random_string()
        profile_1.name_visible     = True
        profile_1.location         = utils.random_string()
        profile_1.location_visible = False
        profile_1.picture_id       = utils.random_string()
        profile_1.picture_visible  = True
        profile_1.save()

        profile_2 = Profile()
        profile_2.global_id        = utils.calc_unique_global_id()
        profile_2.account_secret   = utils.random_string()
        profile_2.name             = utils.random_string()
        profile_2.name_visible     = True
        profile_2.location         = utils.random_string()
        profile_2.location_visible = False
        profile_2.picture_id       = utils.random_string()
        profile_2.picture_visible  = True
        profile_2.save()

        # Create a conversation between these two users.

        conversation = Conversation()
        conversation.global_id_1    = profile_1.global_id
        conversation.global_id_2    = profile_2.global_id
        conversation.hidden_1       = False
        conversation.hidden_2       = False
        conversation.encryption_key = encryption.generate_random_key()
        conversation.last_message   = utils.random_string()
        conversation.last_timestamp = timezone.now()
        conversation.num_unread_1   = 0
        conversation.num_unread_2   = 0
        conversation.save()

        # Create two random Ripple account IDs.

        sender_account_id    = utils.random_string()
        recipient_account_id = utils.random_string()

        # Create a test message with an embedded action.

        message = Message()
        message.conversation         = conversation
        message.hash                 = utils.random_string()
        message.timestamp            = timezone.now()
        message.sender_global_id     = profile_1.global_id
        message.recipient_global_id  = profile_2.global_id
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

        # Ask the "/changes" endpoint for the current anchor value.

        headers = utils.calc_hmac_headers(
            method="GET",
            url="/api/changes",
            body="",
            account_secret=profile_1.account_secret
        )

        url = "/api/changes?my_global_id=" + profile_1.global_id
        response = self.client.get(url, "", content_type="application/json",
                                   **headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], "application/json")
        data = json.loads(response.content)
        self.assertItemsEqual(data.keys(), ["next_anchor"])

        anchor = data['next_anchor']

        # Ask the API to update the message.

        request = json.dumps({'message' : {'hash'      : message.hash,
                                           'processed' : True}})

        headers = utils.calc_hmac_headers(
            method="PUT",
            url="/api/message",
            body=request,
            account_secret=profile_2.account_secret
        )

        response = self.client.put("/api/message",
                                   request,
                                   content_type="application/json",
                                   **headers)
        self.assertEqual(response.status_code, 200)

        # Now ask the "/changes" endpoint for the things that have changed
        # since the anchor was calculated.

        headers = utils.calc_hmac_headers(
            method="GET",
            url="/api/changes",
            body="",
            account_secret=profile_1.account_secret
        )

        url = "/api/changes?my_global_id=" + profile_1.global_id \
                              + "&anchor=" + anchor

        response = self.client.get(url,
                                   **headers)
        if response.status_code != 200:
            print response.content
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], "application/json")
        data = json.loads(response.content)
        self.assertItemsEqual(data.keys(), ["changes", "next_anchor"])

        # Check that the changes includes the updated message.

        found = False
        for change in data['changes']:
            if change['type'] == "message":
                msg = change['data']
                if (msg['sender_global_id'] == profile_1.global_id and
                    msg['recipient_global_id'] == profile_2.global_id):
                    found = True

        self.assertTrue(found)

