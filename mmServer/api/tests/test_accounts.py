""" mmServer.api.tests.test_accounts

    This module implements various unit tests for the "Account" endpoint.
"""
import logging

import django.test
from django.utils import timezone

import simplejson as json

from mmServer.shared.models import *
from mmServer.shared.lib    import utils
from mmServer.api.tests     import apiTestHelpers

#############################################################################

class AccountTestCase(django.test.TestCase):
    """ Unit tests for the "Account" resource.
    """
    def test_get_account_with_no_contents(self):
        """ Test the logic of retrieving an account which has no contents.
        """
        # Create a dummy profile for testing.

        profile = apiTestHelpers.create_profile()

        # Calculate the HMAC authentication headers we need to make an
        # authenticated request.

        headers = utils.calc_hmac_headers(
            method="GET",
            url="/api/account",
            body="",
            account_secret=profile.account_secret
        )

        # Ask the "GET api/account" endpoint to return the user's account
        # details, using the HMAC authentication headers.

        response = self.client.get("/api/account" +
                                   "?global_id=" + profile.global_id,
                                   **headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], "application/json")

        data = json.loads(response.content)

        # Check that the expected data was returned.

        self.assertIsInstance(data, dict)
        self.assertItemsEqual(data.keys(), ["account"])
        self.assertIsInstance(data['account'], dict)
        self.assertItemsEqual(data['account'].keys(), ["balance"])
        self.assertEqual(data['account']['balance'], 0)

    # -----------------------------------------------------------------------

    def test_get_account_transactions(self):
        """ Test the logic of retrieving an account's transactions.
        """
        # Create a dummy profile for testing.

        profile = apiTestHelpers.create_profile()

        # Get or create the Ripple Holding account.

        try:
            holding_account = Account.objects.get(
                                    type=Account.TYPE_RIPPLE_HOLDING)
        except Account.DoesNotExist:
            holding_account = Account()
            holding_account.global_id        = None
            holding_account.type             = Account.TYPE_RIPPLE_HOLDING
            holding_account.balance_in_drops = 0
            holding_account.save()

        # Create an account for the profile's owner, with a dummy transaction.

        user_account = Account()
        user_account.global_id        = profile.global_id
        user_account.type             = Account.TYPE_USER
        user_account.balance_in_drops = 0
        user_account.save()

        transaction = Transaction()
        transaction.timestamp       = timezone.now()
        transaction.created_by      = user_account
        transaction.status          = Transaction.STATUS_SUCCESS
        transaction.type            = Transaction.TYPE_DEPOSIT
        transaction.amount_in_drops = 100
        transaction.debit_account   = holding_account
        transaction.credit_account  = user_account
        transaction.save()

        # Update the account balances to allow for the new transaction.

        holding_account.balance_in_drops = -100
        holding_account.save()

        user_account.balance_in_drops = 100
        user_account.save()

        # Calculate the HMAC authentication headers we need to make an
        # authenticated request.

        headers = utils.calc_hmac_headers(
            method="GET",
            url="/api/account",
            body="",
            account_secret=profile.account_secret
        )

        # Ask the "GET api/account" endpoint to return the user's account
        # details, using the HMAC authentication headers.

        response = self.client.get("/api/account" +
                                   "?global_id=" + profile.global_id +
                                   "&transactions=all",
                                   **headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], "application/json")

        data = json.loads(response.content)

        # Check that the expected data was returned.

        self.assertIsInstance(data, dict)
        self.assertItemsEqual(data.keys(), ["account"])
        self.assertIsInstance(data['account'], dict)
        self.assertItemsEqual(data['account'].keys(),
                              ["balance", "transactions"])
        self.assertEqual(data['account']['balance'], 100)
        self.assertEqual(len(data['account']['transactions']), 1)
        self.assertEqual(data['account']['transactions'][0]['type'], "DEPOSIT")
        self.assertEqual(data['account']['transactions'][0]['amount'], 100)

    # -----------------------------------------------------------------------

    def test_get_account_transaction_totals(self):
        """ Test the logic of retrieving an account's transaction totals.
        """
        # Create a dummy profile for testing.

        profile = apiTestHelpers.create_profile()

        # Get or create the Ripple Holding account.

        try:
            holding_account = Account.objects.get(
                                    type=Account.TYPE_RIPPLE_HOLDING)
        except Account.DoesNotExist:
            holding_account = Account()
            holding_account.global_id        = None
            holding_account.type             = Account.TYPE_RIPPLE_HOLDING
            holding_account.balance_in_drops = 0
            holding_account.save()

        # Get or create the MessageMe account.

        try:
            messageme_account = Account.objects.get(
                                      type=Account.TYPE_MESSAGEME)
        except Account.DoesNotExist:
            messageme_account = Account()
            messageme_account.global_id        = None
            messageme_account.type             = Account.TYPE_MESSAGEME
            messageme_account.balance_in_drops = 0
            messageme_account.save()

        # Create an account for the profile's owner, with 3 dummy transactions.

        user_account = Account()
        user_account.global_id        = profile.global_id
        user_account.type             = Account.TYPE_USER
        user_account.balance_in_drops = 0
        user_account.save()

        transaction = Transaction()
        transaction.timestamp       = timezone.now()
        transaction.created_by      = user_account
        transaction.status          = Transaction.STATUS_SUCCESS
        transaction.type            = Transaction.TYPE_DEPOSIT
        transaction.amount_in_drops = 100
        transaction.debit_account   = holding_account
        transaction.credit_account  = user_account
        transaction.save()

        transaction = Transaction()
        transaction.timestamp       = timezone.now()
        transaction.created_by      = user_account
        transaction.status          = Transaction.STATUS_SUCCESS
        transaction.type            = Transaction.TYPE_SYSTEM_CHARGE
        transaction.amount_in_drops = 1
        transaction.debit_account   = user_account
        transaction.credit_account  = messageme_account
        transaction.save()

        transaction = Transaction()
        transaction.timestamp       = timezone.now()
        transaction.created_by      = user_account
        transaction.status          = Transaction.STATUS_SUCCESS
        transaction.type            = Transaction.TYPE_WITHDRAWAL
        transaction.amount_in_drops = 20
        transaction.debit_account   = user_account
        transaction.credit_account  = holding_account
        transaction.save()

        # Update the account balances to allow for the new transactions.

        holding_account.balance_in_drops = -80
        holding_account.save()

        messageme_account.balance_in_drops = 1
        messageme_account.save()

        user_account.balance_in_drops = 79
        user_account.save()

        # Calculate the HMAC authentication headers we need to make an
        # authenticated request.

        headers = utils.calc_hmac_headers(
            method="GET",
            url="/api/account",
            body="",
            account_secret=profile.account_secret
        )

        # Ask the "GET api/account" endpoint to return the user's account
        # details, using the HMAC authentication headers.

        response = self.client.get("/api/account" +
                                   "?global_id=" + profile.global_id +
                                   "&totals=yes",
                                   **headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], "application/json")

        data = json.loads(response.content)

        # Check that the expected data was returned.

        self.assertIsInstance(data, dict)
        self.assertItemsEqual(data.keys(), ["account"])
        self.assertIsInstance(data['account'], dict)
        self.assertItemsEqual(data['account'].keys(),
                              ["balance", "totals"])
        self.assertEqual(data['account']['balance'], 79)
        self.assertIsInstance(data['account']['totals'], dict)
        self.assertItemsEqual(data['account']['totals'].keys(),
                              ["deposits", "withdrawals", "system_charges",
                              "recipient_charges", "adjustments"])
        self.assertEqual(data['account']['totals']['deposits'], 100)
        self.assertEqual(data['account']['totals']['withdrawals'], 20)
        self.assertEqual(data['account']['totals']['system_charges'], 1)
        self.assertEqual(data['account']['totals']['recipient_charges'], 0)
        self.assertEqual(data['account']['totals']['adjustments'], 0)

