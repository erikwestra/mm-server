""" mmServer.api.views.account

    This module implements the "account" endpoint for the mmServer.api
    application.
"""
import logging

from django.http                  import *
from django.views.decorators.csrf import csrf_exempt
from django.db.models             import Q

import simplejson as json

from mmServer.shared.models import *
from mmServer.shared.lib    import utils

#############################################################################

logger = logging.getLogger(__name__)

#############################################################################

@csrf_exempt
def endpoint(request):
    """ Respond to the "/api/account" endpoint.

        This view function simply selects an appropriate handler based on the
        HTTP method.
    """
    try:
        if request.method == "GET":
            return account_GET(request)
        else:
            return HttpResponseNotAllowed(["GET"])
    except:
        return utils.exception_response()

#############################################################################

def account_GET(request):
    """ Respond to the "GET /api/account" API request.

        This is used to retrieve a user's account details.
    """
    if not utils.has_hmac_headers(request):
        return HttpResponseForbidden()

    # Get the request parameters.

    if "global_id" in request.GET:
        global_id_param = request.GET['global_id']
    else:
        return HttpResponseBadRequest("Missing 'global_id' parameter.")

    if "transactions" in request.GET:
        transactions_param = request.GET['transactions']
        if transactions_param != "all":
            for ch in transactions_param:
                if ch not in ["D", "W", "S", "R", "A"]:
                    return HttpResponseBadRequest("Invalid 'transactions' " +
                                                  "parameter.")
    else:
        transactions_param = None

    if "tpp" in request.GET:
        try:
            tpp_param = int(request.GET['tpp'])
        except ValueError:
            return HttpResponseBadRequest("Invalid 'tpp' parameter.")
    else:
        tpp_param = 20

    if "page" in request.GET:
        try:
            page_param = int(request.GET['page'])
        except ValueError:
            return HttpResponseBadRequest("Invalid 'page' parameter.")
    else:
        page_param = 0

    if "totals" in request.GET:
        if request.GET['totals'] == "yes":
            totals_param = "yes"
        elif request.GET['totals'] == "charges_by_conversation":
            return HttpResponseBadRequest("charges_by_conversation is not " +
                                          "implemented yet")
        else:
            return HttpResponseBadRequest("Invalid 'totals' parameter.")
    else:
        totals_param = None

    # Get the user's profile, and check the HMAC authentication details.

    try:
        profile = Profile.objects.get(global_id=global_id_param)
    except Profile.DoesNotExist:
        return HttpResponseBadRequest("There is no profile for that global ID")

    if not utils.check_hmac_authentication(request, profile.account_secret):
        return HttpResponseForbidden()

    # Get the user's Account record.  If it doesn't exist, create one.

    try:
        account = Account.objects.get(type=Account.TYPE_USER,
                                      global_id=global_id_param)
    except Account.DoesNotExist:
        account = Account()
        account.type             = Account.TYPE_USER
        account.global_id        = global_id_param
        account.balance_in_drops = 0
        account.save()

    # Start preparing the results to return back to the caller.

    response = {
        'account': {
            'balance' : account.balance_in_drops
        }
    }

    # If we've been asked for them, get the desired set of transactions for
    # this account.

    if transactions_param != None:
        trans_types = []
        if transactions_param == "all" or "D" in transactions_param:
            trans_types.append(Transaction.TYPE_DEPOSIT)
        if transactions_param == "all" or "W" in transactions_param:
            trans_types.append(Transaction.TYPE_WITHDRAWAL)
        if transactions_param == "all" or "S" in transactions_param:
            trans_types.append(Transaction.TYPE_SYSTEM_CHARGE)
        if transactions_param == "all" or "R" in transactions_param:
            trans_types.append(Transaction.TYPE_RECIPIENT_CHARGE)
        if transactions_param == "all" or "A" in transactions_param:
            trans_types.append(Transaction.TYPE_ADJUSTMENT)

        query = (Q(type__in=trans_types) &
                 Q(status=Transaction.STATUS_SUCCESS) &
                 (Q(debit_account=account) | Q(credit_account=account)))

        results = Transaction.objects.filter(query).order_by("-timestamp")

        first = page_param * tpp_param
        last = (page_param+1) * tpp_param

        transactions = []
        for transaction in results[first:last]:
            trans = {}
            trans['transaction_id'] = transaction.id
            trans['timestamp']      = utils.datetime_to_unix_timestamp(
                                                transaction.timestamp)
            trans['type']           = Transaction.TYPE_MAP[transaction.type]
            trans['amount']         = transaction.amount_in_drops

            if transaction.debit_account == account:
                other_account = transaction.credit_account
            elif transaction.credit_account == account:
                other_account = transaction.debit_account
            else:
                raise RuntimeError("Should never happen")

            trans['other_account_type'] = Account.TYPE_MAP[other_account.type]
            if other_account.type == Account.TYPE_USER:
                trans['other_account_global_id'] = other_account.global_id

            if transaction.message_hash != None:
                trans['message_hash'] = transaction.message_hash

            transactions.append(trans)

        response['account']['transactions'] = transactions

    # If we've been asked to calculate them, get the transaction totals for
    # this account.

    if totals_param == "yes":
        totals = {'deposits'          : 0,
                  'withdrawals'       : 0,
                  'system_charges'    : 0,
                  'recipient_charges' : 0,
                  'adjustments'       : 0}

        query = (Q(status=Transaction.STATUS_SUCCESS) &
                 (Q(debit_account=account) | Q(credit_account=account)))

        for transaction in Transaction.objects.filter(query):
            if transaction.type == Transaction.TYPE_DEPOSIT:
                totals['deposits'] += transaction.amount_in_drops
            elif transaction.type == Transaction.TYPE_WITHDRAWAL:
                totals['withdrawals'] += transaction.amount_in_drops
            elif transaction.type == Transaction.TYPE_SYSTEM_CHARGE:
                totals['system_charges'] += transaction.amount_in_drops
            elif transaction.type == Transaction.TYPE_RECIPIENT_CHARGE:
                totals['recipient_charges'] += transaction.amount_in_drops
            elif transaction.type == Transaction.TYPE_ADJUSTMENT:
                if transaction.debit_account == account:
                    totals['adjustments'] -= transaction.amount_in_drops
                elif transaction.credit_account == account:
                    totals['adjustments'] -= transaction.amount_in_drops

        response['account']['totals'] = totals

    # Finally, return the response back to the caller.

    return HttpResponse(json.dumps(response),
                        mimetype="application/json")

