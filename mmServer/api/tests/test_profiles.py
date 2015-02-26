""" mmServer.api.tests.test_profiles

    This module implements various unit tests for the "profile" resource's API
    endpoints.
"""
import logging

import django.test

import simplejson as json

from mmServer.shared.models import *
from mmServer.shared.lib    import utils
from mmServer.api.tests     import apiTestHelpers

#############################################################################

class ProfileTestCase(django.test.TestCase):
    """ Unit tests for the "Profile" resource.
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

        profile = apiTestHelpers.create_profile()

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

        profile = apiTestHelpers.create_profile()

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
        self.assertItemsEqual(data.keys(),
                              ["global_id",
                               "name",
                               "name_visible",
                               "email",
                               "phone",
                               "address_1",
                               "address_1_visible",
                               "address_2",
                               "address_2_visible",
                               "city",
                               "city_visible",
                               "state_province_or_region",
                               "state_province_or_region_visible",
                               "zip_or_postal_code",
                               "zip_or_postal_code_visible",
                               "country",
                               "country_visible",
                               "date_of_birth",
                               "social_security_number_last_4_digits",
                               "bio",
                               "bio_visible",
                               "picture_id",
                               "picture_id_visible"])

        self.assertEqual(data['global_id'],          profile.global_id)
        self.assertEqual(data['name'],               profile.name)
        self.assertEqual(data['name_visible'],       profile.name_visible)
        self.assertEqual(data['email'],              profile.email)
        self.assertEqual(data['phone'],              profile.phone)
        self.assertEqual(data['address_1'],          profile.address_1)
        self.assertEqual(data['address_1_visible'],  profile.address_1_visible)
        self.assertEqual(data['address_2'],          profile.address_2)
        self.assertEqual(data['address_2_visible'],  profile.address_2_visible)
        self.assertEqual(data['city'],               profile.city)
        self.assertEqual(data['city_visible'],       profile.city_visible)
        self.assertEqual(data['state_province_or_region'],
                         profile.state_province_or_region)
        self.assertEqual(data['state_province_or_region_visible'],
                         profile.state_province_or_region_visible)
        self.assertEqual(data['zip_or_postal_code'],
                         profile.zip_or_postal_code)
        self.assertEqual(data['zip_or_postal_code_visible'],
                        profile.zip_or_postal_code_visible)
        self.assertEqual(data['country'],            profile.country)
        self.assertEqual(data['country_visible'],    profile.country_visible)
        self.assertEqual(data['date_of_birth'],
                         utils.date_to_string(profile.date_of_birth))
        self.assertEqual(data['social_security_number_last_4_digits'],
                         profile.social_security_number_last_4_digits)
        self.assertEqual(data['bio'],                profile.bio)
        self.assertEqual(data['bio_visible'],        profile.bio_visible)
        self.assertEqual(data['picture_id'],         profile.picture_id)
        self.assertEqual(data['picture_id_visible'], profile.picture_id_visible)

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
            profile = apiTestHelpers.create_profile(name=name)

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
            profile = apiTestHelpers.create_profile(name=name)

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

        profile = apiTestHelpers.create_profile()

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

        data = {'global_id'                            : global_id,
                'name'                                 : utils.random_string(),
                'name_visible'                         : True,
                'email'                                : utils.random_string(),
                'phone'                                : utils.random_string(),
                'address_1'                            : utils.random_string(),
                'address_1_visible'                    : False,
                'address_2'                            : utils.random_string(),
                'address_2_visible'                    : False,
                'city'                                 : utils.random_string(),
                'city_visible'                         : False,
                'state_province_or_region'             : utils.random_string(),
                'state_province_or_region_visible'     : False,
                'zip_or_postal_code'                   : utils.random_string(),
                'zip_or_postal_code_visible'           : False,
                'country'                              : utils.random_string(),
                'country_visible'                      : False,
                'date_of_birth'                        : "1965-05-07",
                'social_security_number_last_4_digits' : "1234",
                'bio'                                  : utils.random_string(),
                'bio_visible'                          : False,
                'picture_id'                           : utils.random_string(),
                'picture_id_visible'                   : True}

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

        self.assertEqual(profile.global_id,          global_id)
        self.assertEqual(profile.account_secret,     account_secret)
        self.assertEqual(profile.name,               data['name'])
        self.assertEqual(profile.name_visible,       data['name_visible'])
        self.assertEqual(profile.email,              data['email'])
        self.assertEqual(profile.phone,              data['phone'])
        self.assertEqual(profile.address_1,          data['address_1'])
        self.assertEqual(profile.address_1_visible,  data['address_1_visible'])
        self.assertEqual(profile.address_2,          data['address_2'])
        self.assertEqual(profile.address_2_visible,  data['address_2_visible'])
        self.assertEqual(profile.city,               data['city'])
        self.assertEqual(profile.city_visible,       data['city_visible'])
        self.assertEqual(profile.state_province_or_region,
                         data['state_province_or_region'])
        self.assertEqual(profile.state_province_or_region_visible,
                         data['state_province_or_region_visible'])
        self.assertEqual(profile.zip_or_postal_code,
                         data['zip_or_postal_code'])
        self.assertEqual(profile.zip_or_postal_code_visible,
                         data['zip_or_postal_code_visible'])
        self.assertEqual(profile.country,            data['country'])
        self.assertEqual(profile.country_visible,    data['country_visible'])
        self.assertEqual(profile.date_of_birth,
                         utils.string_to_date(data['date_of_birth']))
        self.assertEqual(profile.social_security_number_last_4_digits,
                         data['social_security_number_last_4_digits'])
        self.assertEqual(profile.bio,                data['bio'])
        self.assertEqual(profile.bio_visible,        data['bio_visible'])
        self.assertEqual(profile.picture_id,         data['picture_id'])
        self.assertEqual(profile.picture_id_visible, data['picture_id_visible'])

    # -----------------------------------------------------------------------

    def test_update_profile(self):
        """ Test the process of updating a user profile.
        """
        # Create a dummy profile for testing.

        profile = apiTestHelpers.create_profile()

        # Calculate some new data to store into the profile.

        new_name                                 = utils.random_string()
        new_name_visible                         = False
        new_email                                = utils.random_string()
        new_phone                                = utils.random_string()
        new_address_1                            = utils.random_string()
        new_address_1_visible                    = True
        new_address_2                            = utils.random_string()
        new_address_2_visible                    = True
        new_city                                 = utils.random_string()
        new_city_visible                         = True
        new_state_province_or_region             = utils.random_string()
        new_state_province_or_region_visible     = True
        new_zip_or_postal_code                   = utils.random_string()
        new_zip_or_postal_code_visible           = True
        new_country                              = utils.random_string()
        new_country_visible                      = True
        new_date_of_birth                        = "1990-09-20"
        new_social_security_number_last_4_digits = "9876"
        new_bio                                  = utils.random_string()
        new_bio_visible                          = True
        new_picture_id                           = utils.random_string()
        new_picture_id_visible                   = False

        # Set up the body of our request.

        request = json.dumps(
           {'name'                       : new_name,
            'name_visible'               : new_name_visible,
            'email'                      : new_email,
            'phone'                      : new_phone,
            'address_1'                  : new_address_1,
            'address_1_visible'          : new_address_1_visible,
            'address_2'                  : new_address_2,
            'address_2_visible'          : new_address_2_visible,
            'city'                       : new_city,
            'city_visible'               : new_city_visible,
            'state_province_or_region'   : new_state_province_or_region,
            'state_province_or_region_visible' :
                                        new_state_province_or_region_visible,
            'zip_or_postal_code'         : new_zip_or_postal_code,
            'zip_or_postal_code_visible' : new_zip_or_postal_code_visible,
            'country'                    : new_country,
            'country_visible'            : new_country_visible,
            'date_of_birth'              : new_date_of_birth,
            'social_security_number_last_4_digits' :
                                    new_social_security_number_last_4_digits,
            'bio'                        : new_bio,
            'bio_visible'                : new_bio_visible,
            'picture_id'                 : new_picture_id,
            'picture_id_visible'         : new_picture_id_visible})

        # Calculate the HMAC authentication headers we need to make an
        # authenticated request.

        headers = utils.calc_hmac_headers(
            method="PUT",
            url="/api/profile/" + profile.global_id,
            body=request,
            account_secret=profile.account_secret
        )

        # Ask the "PUT api/profile/<GLOBAL_ID>" endpoint to update the user's
        # profile, using the HMAC authentication headers.

        response = self.client.put("/api/profile/" + profile.global_id,
                                   request,
                                   content_type="application/json",
                                   **headers)

        self.assertEqual(response.status_code, 200)

        # Check that the profile has been updated.

        profile = Profile.objects.get(global_id=profile.global_id)

        self.assertEqual(profile.name,               new_name)
        self.assertEqual(profile.name_visible,       new_name_visible)
        self.assertEqual(profile.email,              new_email)
        self.assertEqual(profile.phone,              new_phone)
        self.assertEqual(profile.address_1,          new_address_1)
        self.assertEqual(profile.address_1_visible,  new_address_1_visible)
        self.assertEqual(profile.address_2,          new_address_2)
        self.assertEqual(profile.address_2_visible,  new_address_2_visible)
        self.assertEqual(profile.city,               new_city)
        self.assertEqual(profile.city_visible,       new_city_visible)
        self.assertEqual(profile.state_province_or_region,
                         new_state_province_or_region)
        self.assertEqual(profile.state_province_or_region_visible,
                         new_state_province_or_region_visible)
        self.assertEqual(profile.zip_or_postal_code, new_zip_or_postal_code)
        self.assertEqual(profile.zip_or_postal_code_visible,
                         new_zip_or_postal_code_visible)
        self.assertEqual(profile.country,            new_country)
        self.assertEqual(profile.country_visible,    new_country_visible)
        self.assertEqual(profile.date_of_birth,
                         utils.string_to_date(new_date_of_birth))
        self.assertEqual(profile.social_security_number_last_4_digits,
                         new_social_security_number_last_4_digits)
        self.assertEqual(profile.bio,                new_bio)
        self.assertEqual(profile.bio_visible,        new_bio_visible)
        self.assertEqual(profile.picture_id,         new_picture_id)
        self.assertEqual(profile.picture_id_visible, new_picture_id_visible)

    # -----------------------------------------------------------------------

    def test_delete_profile(self):
        """ Test the process of deleting a user profile.
        """
        # Create a dummy profile for testing.

        profile = apiTestHelpers.create_profile()

        # Calculate the HMAC authentication headers we need to make an
        # authenticated request.

        headers = utils.calc_hmac_headers(
            method="DELETE",
            url="/api/profile/" + profile.global_id,
            body="",
            account_secret=profile.account_secret
        )

        # Ask the "DELETE api/profile/<GLOBAL_ID>" endpoint to delete the
        # user's profile, using the HMAC authentication headers.

        response = self.client.delete("/api/profile/" + profile.global_id,
                                      **headers)

        self.assertEqual(response.status_code, 200)

        # Check that the profile has been deleted.

        try:
            profile = Profile.objects.get(global_id=profile.global_id)
        except Profile.DoesNotExist:
            profile = None

        self.assertIsNotNone(profile) # Should simply mark profile as deleted.
        self.assertTrue(profile.deleted)

