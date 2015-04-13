""" mmServer.api.tests.test_transactions

    This module implements various unit tests for the "Transaction" endpoint.
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
    def test_post_transaction_to_account(self):
        """ Test the logic of submitting a transaction to a user's account.
        """
        # Create a dummy profile for testing.

        profile = apiTestHelpers.create_profile()

        # Create a random Ripple account ID.

        ripple_account = utils.random_string()

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

        # Create the body of our request.

        request = json.dumps(
                        {'global_id'      : profile.global_id,
                         'ripple_account' : ripple_account,
                         'type'           : "DEPOSIT",
                         'amount'         : 10,
                         'description'    : "Test Transaction"})

        # Calculate the HMAC authentication headers we need to make an
        # authenticated request.

        headers = utils.calc_hmac_headers(
            method="POST",
            url="/api/transaction",
            body=request,
            account_secret=profile.account_secret
        )

        # Install the mock version of the rippleInterface.request() function.
        # This prevents the RippleInterface module from submitting the
        # transaction to the Ripple network.

        rippleMock = apiTestHelpers.install_mock_ripple_interface()

        # Ask the "POST api/transaction" endpoint to create the transaction.
        # Because this is a "DEPOSIT" transaction, this should create a Ripple
        # transaction transferring funds out of the user's Ripple account and
        # into the MessageMe Ripple Holding Account.

        response = self.client.post("/api/transaction",
                                    request,
                                    content_type="application/json",
                                    **headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], "application/json")

        data = json.loads(response.content)

        # Check that the expected data was returned.

        self.assertIsInstance(data, dict)
        self.assertItemsEqual(data.keys(), ["transaction_id", "status"])
        self.assertEqual(data['status'], "PENDING")

        # Check that the rippleInterface.request() function was called to sign
        # and then submit the transaction.

        self.assertEqual(rippleMock.call_count, 2)
        self.assertEqual(rippleMock.call_args_list[0][0][0], "sign")
        self.assertEqual(rippleMock.call_args_list[1][0][0], "submit")

        # Check that a transaction record was created.

        trans_id = data['transaction_id']

        transaction = Transaction.objects.get(id=data['transaction_id'])
        self.assertEqual(transaction.status, Transaction.STATUS_PENDING)
        self.assertEqual(transaction.created_by.global_id, profile.global_id)
        self.assertEqual(transaction.type,   Transaction.TYPE_DEPOSIT)
        self.assertEqual(transaction.debit_account.type,
                         Account.TYPE_RIPPLE_HOLDING)
        self.assertEqual(transaction.credit_account.global_id,
                         profile.global_id)
        self.assertEqual(transaction.amount_in_drops, 10)

    # -----------------------------------------------------------------------

    def test_get_transaction_finalizes_pending_transaction(self):
        """ Check that "GET api/transaction" finalizes a pending transaction.

            We create a pending transaction, and then make a "GET
            api/transaction" call, mocking out the Ripple interface to pretend
            that a transaction was accepted into the Ripple ledger.  We check
            to ensure that the pending transaction was finalized and appears in
            the list of final transactions.
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

        # Create an account for the profile's owner, with a dummy pending
        # transaction.

        user_account = Account()
        user_account.global_id        = profile.global_id
        user_account.type             = Account.TYPE_USER
        user_account.balance_in_drops = 0
        user_account.save()

        transaction = Transaction()
        transaction.timestamp       = timezone.now()
        transaction.created_by      = user_account
        transaction.status          = Transaction.STATUS_PENDING
        transaction.type            = Transaction.TYPE_DEPOSIT
        transaction.amount_in_drops = 100
        transaction.debit_account   = holding_account
        transaction.credit_account  = user_account
        transaction.save()

        # Calculate the HMAC authentication headers we need to make an
        # authenticated request.

        headers = utils.calc_hmac_headers(
            method="GET",
            url="/api/transaction",
            body="",
            account_secret=profile.account_secret
        )

        # Install the mock version of the rippleInterface.request() function.
        # This prevents the RippleInterface module from submitting a request
        # to the Ripple network.

        rippleMock = apiTestHelpers.install_mock_ripple_interface()

        # Ask the "GET api/transaction" endpoint to check the status of the
        # transaction.  All going well, the endpoint should check with the
        # Ripple server, see that the transaction has gone through, and change
        # the transaction's status to "SUCCESS".

        url = "/api/transaction?global_id=%s&transaction_id=%d" \
            % (profile.global_id, transaction.id)

        response = self.client.get(url, "", **headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], "application/json")

        data = json.loads(response.content)

        # Check that the expected data was returned.

        self.assertIsInstance(data, dict)
        self.assertItemsEqual(data.keys(), ["status"])
        self.assertEqual(data['status'], "SUCCESS")

        # Check that the rippleInterface.request() function was called to check
        # the transaction status.

        transaction_hash = transaction.ripple_transaction_hash

        self.assertEqual(rippleMock.call_count, 1)
        rippleMock.asset_called_with('tx',
                                     transaction=transaction_hash,
                                     binary=False)

        # Get the updated Transaction record.

        transaction = Transaction.objects.get(id=transaction.id)

        # Finally, check that the transaction's status has been updated.

        self.assertEqual(transaction.status, Transaction.STATUS_SUCCESS)

