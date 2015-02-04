""" mmServer.api.tests.test_pictures

    This module implements various unit tests for the "picture" resource's API
    endpoints.
"""
import base64

import django.test
import simplejson as json

from mmServer.shared.models import *
from mmServer.shared.lib    import utils

#############################################################################

class PictureTestCase(django.test.TestCase):
    """ Unit tests for the "Picture" resource.
    """
    def test_get_picture(self):
        """ Test the logic of retrieving a picture.
        """
        # Create a dummy picture for testing.

        picture_data = utils.random_string(min_length=10000, max_length=20000)

        picture = Picture()
        picture.picture_id       = utils.calc_unique_picture_id()
        picture.deleted          = False
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

        # Check that the picture has been updated.

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

        # Check that the picture has been marked as deleted.

        try:
            picture = Picture.objects.get(picture_id=picture_id)
        except Picture.DoesNotExist:
            picture = None

        self.assertIsNotNone(picture)    # Picture should still exist...
        self.assertTrue(picture.deleted) # ...but be marked as deleted.

