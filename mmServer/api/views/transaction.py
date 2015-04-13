""" mmServer.api.views.transaction

    This module implements the "transaction endpoint for the mmServer.api
    application.
"""
import logging

from django.http                  import *
from django.views.decorators.csrf import csrf_exempt
from django.db.models             import Q
from django.conf                  import settings
from django.utils                 import timezone

import simplejson as json

from mmServer.shared.models import *
from mmServer.shared.lib    import utils, transactionHandler, encryption
from mmServer.shared.lib    import rippleInterface

#############################################################################

logger = logging.getLogger(__name__)

#############################################################################

@csrf_exempt
def endpoint(request):
    """ Respond to the "/api/transaction" endpoint.

        This view function simply selects an appropriate handler based on the
        HTTP method.
    """
    try:
        if request.method == "GET":
            return transaction_GET(request)
        elif request.method == "POST":
            return transaction_POST(request)
        else:
            return HttpResponseNotAllowed(["GET", "POST"])
    except:
        return utils.exception_response()

#############################################################################

def transaction_GET(request):
    """ Respond to the "GET /api/transaction" API request.

        This is used to check the current status of a pending transaction.
    """
    if not utils.has_hmac_headers(request):
        return HttpResponseForbidden()

    # Get the request parameters.

    if "global_id" in request.GET:
        global_id = request.GET['global_id']
    else:
        return HttpResponseBadRequest("Missing 'global_id' parameter.")

    if "transaction_id" in request.GET:
        transaction_id = request.GET['transaction_id']
    else:
        return HttpResponseBadRequest("Missing 'transaction_id' parameter.")

    # Get the user's profile, and check the HMAC authentication details.

    try:
        profile = Profile.objects.get(global_id=global_id)
    except Profile.DoesNotExist:
        return HttpResponseBadRequest("There is no profile for that global ID")

    if not utils.check_hmac_authentication(request, profile.account_secret):
        return HttpResponseForbidden()

    # Get the desired Transaction record.

    try:
        transaction = Transaction.objects.get(id=transaction_id)
    except Transaction.DoesNotExist:
        return HttpResponseNotFound()

    # Check that this user is the creator of this transaction.

    if transaction.created_by.global_id != global_id:
        return HttpResponseBadRequest("You didn't create this transaction!")

    # If the transaction is pending, ask the Ripple network for the current
    # transaction status.

    cur_status = transaction.status

    if cur_status == Transaction.STATUS_PENDING:
        transactionHandler.check_pending_ripple_transaction(transaction)

    # If the transaction went through, update the affected account balances.

    if (cur_status == Transaction.STATUS_PENDING and
        transaction.status == Transaction.STATUS_SUCCESS):
        transactionHandler.update_account_balance(transaction.debit_account)
        transactionHandler.update_account_balance(transaction.credit_account)

    # Calculate the response to send back to the caller.

    response = {'status' : Transaction.STATUS_MAP[transaction.status]}

    if transaction.status == Transaction.STATUS_FAILED:
        if transaction.error != None:
            response['error'] = transaction.error

    # Finally, send back the response.

    return HttpResponse(json.dumps(response),
                        mimetype="application/json")

#############################################################################

def transaction_POST(request):
    """ Respond to the "POST /api/transaction" API request.

        This is used to submit a transaction for processing.
    """
    if not utils.has_hmac_headers(request):
        return HttpResponseForbidden()

    # Get the request parameters from the body of our request.

    if request.META['CONTENT_TYPE'] != "application/json":
        return HttpResponseBadRequest()

    params = json.loads(request.body)

    if "global_id" in params:
        global_id = params['global_id']
    else:
        return HttpResponseBadRequest("Missing 'global_id' value.")

    if "ripple_account" in params:
        ripple_account = params['ripple_account']
    else:
        return HttpResponseBadRequest("Missing 'ripple_account' value.")

    if "type" in params:
        if params['type'] == "DEPOSIT":
            trans_type = Transaction.TYPE_DEPOSIT
        elif params['type'] == "WITHDRAWAL":
            trans_type = Transaction.TYPE_WITHDRAWAL
        else:
            return HttpResponseBadRequest("Invalid 'type' value.")
    else:
        return HttpResponseBadRequest("Missing 'type' value.")

    if "amount" in params:
        try:
            amount_in_drops = int(params['amount'])
        except ValueError:
            return HttpResponseBadRequest("Invalid 'amount' value.")
    else:
        return HttpResponseBadRequest("Missing 'amount' value.")

    if "description" in params:
        description = params['description']
    else:
        description = None

    # Get the user's profile, and check the HMAC authentication details.

    try:
        profile = Profile.objects.get(global_id=global_id)
    except Profile.DoesNotExist:
        return HttpResponseBadRequest("There is no profile for that global ID")

    if not utils.check_hmac_authentication(request, profile.account_secret):
        return HttpResponseForbidden()

    # Get the user's Account record.  If it doesn't exist, create one.

    try:
        account = Account.objects.get(type=Account.TYPE_USER,
                                      global_id=global_id)
    except Account.DoesNotExist:
        account = Account()
        account.type             = Account.TYPE_USER
        account.global_id        = global_id
        account.balance_in_drops = 0
        account.save()

    # Get the MessageMe Ripple Holding Account record, creating it if it
    # doesn't exist.

    try:
        holding_account = Account.objects.get(
                                type=Account.TYPE_RIPPLE_HOLDING)
    except Account.DoesNotExist:
        holding_account = Account()
        holding_account.global_id        = None
        holding_account.type             = Account.TYPE_RIPPLE_HOLDING
        holding_account.balance_in_drops = 0
        holding_account.save()

    # Create the Transaction record for this transaction.  Note that we assume
    # that the transaction will be pending, but may change this if an error
    # occurs.

    transaction = Transaction()
    transaction.timestamp               = timezone.now()
    transaction.created_by              = account
    transaction.status                  = Transaction.STATUS_PENDING #initially
    transaction.type                    = Transaction.TYPE_DEPOSIT
    transaction.amount_in_drops         = amount_in_drops
    transaction.debit_account           = holding_account
    transaction.credit_account          = account
    transaction.ripple_transaction_hash = None # initially
    transaction.message_hash            = None
    transaction.description             = description
    transaction.error                   = None # initially

    error = None # initially.

    if trans_type == Transaction.TYPE_DEPOSIT:

        # The user is making a deposit -> create a Ripple transaction to
        # transfer the funds into the MessageMe Ripple Holding Account.  We
        # don't actually credit the user's MessageMe account until this
        # transaction has been confirmed in the Ripple ledger.

        ripple_transaction = {
            'TransactionType' : "Payment",
            'Account'         : ripple_account,
            'Destination'     : settings.RIPPLE_HOLDING_ACCOUNT,
            'Amount'          : str(amount_in_drops),
            'Fee'             : 100000,
        }

        # Ask the Ripple network to sign our transaction, using the user's
        # account secret.

        response = rippleInterface.request("sign",
                                           tx_json=ripple_transaction,
                                           secret=profile.account_secret)
        if response == None:
            error = "Ripple server failed to respond when signing " \
                  + "the transaction"
        elif response['status'] != "success":
            error = "Ripple server error signing transaction: %s" \
                  % response['error']

        # Now attempt to submit the transaction to the Ripple ledger.

        if error == None:
            tx_blob = response['result']['tx_blob']

            response = rippleInterface.request("submit",
                                               tx_blob=tx_blob,
                                               fail_hard=True)

            if response == None:
                error = "Ripple server failed to respond when submitting " \
                      + "transaction"
            elif response['status'] != "success":
                error = "Ripple server error submittting transaction: " \
                      + response['error']

        if error == None:
            transaction.ripple_transaction_hash = \
                response['result']['tx_json']['hash']

    elif trans_type == Transaction.TYPE_WITHDRAWAL:

        # The user is attempting to withdraw some funds from their MessageMe
        # account.  In this case, we only allow the withdrawal if there are
        # sufficient funds in their account.  We debit the user's MessageMe
        # account right away, and then credit the funds again if the Ripple
        # transaction fails.

        if account.balance_in_drops < amount_in_drops:
            error = "Insufficient funds"

        if error == None:

            # Attempt to create a Ripple transaction transferring the funds
            # from the MessageMe Ripple Holding Account, back into the user's
            # Ripple account.

            ripple_transaction = {
                'TransactionType' : "Payment",
                'Account'         : settings.RIPPLE_HOLDING_ACCOUNT,
                'Destination'     : ripple_account,
                'Amount'          : str(amount_in_drops),
                'Fee'             : 100000,
            }

            # Ask the Ripple network to sign our transaction, using the user's
            # account secret.

            response = rippleInterface.request("sign",
                                               tx_json=ripple_transaction,
                                               secret=profile.account_secret)
            if response == None:
                error = "Ripple server failed to respond when signing " \
                      + "the transaction"
            elif response['status'] != "success":
                error = "Ripple server error signing transaction: %s" \
                      % response['error']

            # Now attempt to submit the transaction to the Ripple ledger.

            if error == None:
                tx_blob = response['result']['tx_blob']

                response = rippleInterface.request("submit",
                                                   tx_blob=tx_blob,
                                                   fail_hard=True)

                if response == None:
                    error = "Ripple server failed to respond when " \
                          + "submitting transaction"
                elif response['status'] != "success":
                    error = "Ripple server error submittting transaction: " \
                          + response['error']

        if error == None:
            transaction.ripple_transaction_hash = \
                response['result']['tx_json']['hash']

    # If our attempt to sign and submit the Ripple transaction failed, mark
    # our internal transaction as having failed right away.

    if error != None:
        transaction.status = Transaction.STATUS_FAILED
        transaction.error  = error

    # Save our transaction, and get the internal ID for the transaction.

    transaction.save()
    transaction_id = transaction.id

    # Finally, return our response back to the caller.

    response = {
        'status'         : Transaction.STATUS_MAP[transaction.status],
        'transaction_id' : transaction_id
    }

    if transaction.status == Transaction.STATUS_FAILED:
        response['error'] = transaction.error

    return HttpResponse(json.dumps(response),
                        mimetype="application/json")

