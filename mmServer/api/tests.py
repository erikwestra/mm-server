""" mmServer.api.tests

    This module implements the various unit tests for the mmServer.api
    application.
"""
import simplejson as json

from django.utils import unittest
import django.test

from mmServer.shared.models import *
from mmServer.shared.lib    import utils

#############################################################################

class ProfileTestCase(django.test.TestCase):
    """ Unit tests for the "api/profile" endpoint.
    """
    def test_get_public_profile(self):
        """ Test the logic of retrieving a user's public profile.
        """
        # Create a dummy profile for testing.

        profile = Profile()
        profile.global_id           = utils.calc_unique_global_id()
        profile.account_secret      = utils.random_string()
        profile.name                = utils.random_string()
        profile.name_visible        = True
        profile.location            = utils.random_string()
        profile.location_visible    = False
        profile.picture_url         = utils.random_string()
        profile.picture_url_visible = True
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
                                            "picture_url"])

        self.assertEqual(data['global_id'],   profile.global_id)
        self.assertEqual(data['name'],        profile.name)
        self.assertEqual(data['picture_url'], profile.picture_url)

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
        profile.global_id           = utils.calc_unique_global_id()
        profile.account_secret      = utils.random_string()
        profile.name                = utils.random_string()
        profile.name_visible        = True
        profile.location            = utils.random_string()
        profile.location_visible    = False
        profile.picture_url         = utils.random_string()
        profile.picture_url_visible = True
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
                                            "picture_url",
                                            "picture_url_visible"])

        self.assertEqual(data['global_id'],        profile.global_id)
        self.assertEqual(data['name'],             profile.name)
        self.assertEqual(data['name_visible'],     profile.name_visible)
        self.assertEqual(data['location'],         profile.location)
        self.assertEqual(data['location_visible'], profile.location_visible)
        self.assertEqual(data['picture_url'],      profile.picture_url)
        self.assertEqual(data['picture_url_visible'],
                                                   profile.picture_url_visible)

    # -----------------------------------------------------------------------

    def test_invalid_hmac(self):
        """ Check that using an invalid HMAC authentication fails.
        """
        # Create a dummy profile for testing.

        profile = Profile()
        profile.global_id           = utils.calc_unique_global_id()
        profile.account_secret      = utils.random_string()
        profile.name                = utils.random_string()
        profile.name_visible        = True
        profile.location            = utils.random_string()
        profile.location_visible    = False
        profile.picture_url         = utils.random_string()
        profile.picture_url_visible = True
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

        data = {'global_id'           : global_id,
                'name'                : utils.random_string(),
                'name_visible'        : True,
                'location'            : utils.random_string(),
                'location_visible'    : False,
                'picture_url'         : utils.random_string(),
                'picture_url_visible' : True}

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
        self.assertEqual(profile.picture_url,      data['picture_url'])
        self.assertEqual(profile.picture_url_visible,
                                                   data['picture_url_visible'])

    # -----------------------------------------------------------------------

    def test_update_profile(self):
        """ Test the process of updating a user profile.
        """
        # Create a dummy profile for testing.

        global_id      = utils.calc_unique_global_id()
        account_secret = utils.random_string()

        profile = Profile()
        profile.global_id           = global_id
        profile.account_secret      = account_secret
        profile.name                = utils.random_string()
        profile.name_visible        = True
        profile.location            = utils.random_string()
        profile.location_visible    = False
        profile.picture_url         = utils.random_string()
        profile.picture_url_visible = True
        profile.save()

        # Calculate some new data to store into the profile.

        new_name                = utils.random_string()
        new_name_visible        = False
        new_location            = utils.random_string()
        new_location_visible    = True
        new_picture_url         = utils.random_string()
        new_picture_url_visible = False

        # Set up the body of our request.

        request = json.dumps({'name'                : new_name,
                              'name_visible'        : new_name_visible,
                              'location'            : new_location,
                              'location_visible'    : new_location_visible,
                              'picture_url'         : new_picture_url,
                              'picture_url_visible' : new_picture_url_visible})

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

        self.assertEqual(profile.global_id,           global_id)
        self.assertEqual(profile.account_secret,      account_secret)
        self.assertEqual(profile.name,                new_name)
        self.assertEqual(profile.name_visible,        new_name_visible)
        self.assertEqual(profile.location,            new_location)
        self.assertEqual(profile.location_visible,    new_location_visible)
        self.assertEqual(profile.picture_url,         new_picture_url)
        self.assertEqual(profile.picture_url_visible, new_picture_url_visible)

    # -----------------------------------------------------------------------

    def test_delete_profile(self):
        """ Test the process of deleting a user profile.
        """
        # Create a dummy profile for testing.

        global_id      = utils.calc_unique_global_id()
        account_secret = utils.random_string()

        profile = Profile()
        profile.global_id           = global_id
        profile.account_secret      = account_secret
        profile.name                = utils.random_string()
        profile.name_visible        = True
        profile.location            = utils.random_string()
        profile.location_visible    = False
        profile.picture_url         = utils.random_string()
        profile.picture_url_visible = True
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

