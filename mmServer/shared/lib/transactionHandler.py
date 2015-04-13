""" mmServer.shared.lib.transactionHandler

    This module define various functions which work with transactions and the
    Ripple network.
"""
import datetime
import logging

from django.utils import timezone

from mmServer.shared.lib    import rippleInterface
from mmServer.shared.models import *

#############################################################################

logger = logging.getLogger("mmServer")

#############################################################################

def check_pending_ripple_transaction(transaction):
    """ Check the given pending transaction in the Ripple network.

        We ask the Ripple network for the current status of the Ripple
        transaction associated with the given Transaction object.  If the
        associated Ripple transaction is no longer pending, we update the
        Transaction object appropriately.

        Upon completion, the transaction may still be pending, or it may have
        succeeded or failed, depending on the results of submitting the
        transaction to the Ripple ledger.
    """
    trans_hash = transaction.ripple_transaction_hash
    response = rippleInterface.request("tx", transaction=trans_hash,
                                             binary=False)
    if response == None:
        return

    if response['status'] == "error":
        # The Ripple server returned an error.  If the error was "txnNotFound"
        # and the transaction was more than 60 seconds old, mark it as failed
        # so we don't continue to check for transactions which never made it to
        # the Ripple network.

        cutoff = timezone.now() - datetime.timedelta(seconds=60)
        if response['error'] == "txnNotFound":
            if transaction.timestamp < cutoff:
                transaction.status = Transaction.STATUS_FAILED
                transaction.error  = response['error']
                transaction.save()
                return

        # If we get here, we have an ordinary error -> fail the transaction.

        transaction.status = Transaction.STATUS_FAILED
        transaction.error  = response['error_message']
        transaction.save()
        return

    if response['result'].get("validated", False):
        # The Ripple transaction has been validated -> update the status.

        trans_result = response['result']['meta']['TransactionResult']
        if trans_result == "tesSUCCESS":
            transaction.status = Transaction.STATUS_SUCCESS
            transaction.error  = None
        else:
            transaction.status  = Transaction.STATUS_FAILED
            transaction.error = trans_result
        transaction.save()

#############################################################################

def update_account_balance(account):
    """ Recalculate the account balance for the given account.
    """
    balance = 0
    for credit in Transaction.objects.filter(status=Transaction.STATUS_SUCCESS,
                                             credit_account=account):
        balance = balance + credit.amount_in_drops
    for debit in Transaction.objects.filter(status=Transaction.STATUS_SUCCESS,
                                            debit_account=account):
        balance = balance - debit.amount_in_drops

    account.balance_in_drops = balance
    account.save()

