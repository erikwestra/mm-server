""" mmServer.api.views.account

    This module implements the "account" endpoint for the mmServer.api
    application.
"""
import datetime
import logging
import operator

from django.http                  import *
from django.views.decorators.csrf import csrf_exempt
from django.db.models             import Q, Sum, Min, Max

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

    # See if the caller is using the legacy parameters.  If so, use the old
    # logic for returning a summary of the transactions.

    if "global_id" in request.GET and request.GET.get("totals") == "yes":
        return _legacy_account_GET(request)

    # Get the request parameters.

    params = {}

    if "global_id" in request.GET:
        params['global_id'] = request.GET['global_id']
    else:
        return HttpResponseBadRequest("Missing 'global_id' parameter.")

    if "return" in request.GET:
        params['return'] = request.GET['return']
        if params['return'] not in ["balance", "transactions", "totals"]:
            return HttpResponseBadRequest("Invalid 'return' parameter value.")
    else:
        return HttpResponseBadRequest("Missing 'return' parameter.")

    if "group" in request.GET:
        params['group'] = request.GET['group']
        if params['group'] not in ["type", "conversation", "date"]:
            return HttpResponseBadRequest("Invalid 'group' parameter value.")
    else:
        params['group'] = "type"

    if "type" in request.GET:
        params['type'] = request.GET['type']
        if params['type'] not in ["charges_paid", "charges_received",
                                  "deposits", "withdrawals",
                                  "adjustments_paid", "adjustments_received"]:
            return HttpResponseBadRequest("Invalid 'type' parameter value.")

    if "conversation" in request.GET:
        global_id_1 = params['global_id']
        global_id_2 = request.GET['conversation']

        try:
            conversation = Conversation.objects.get(global_id_1=global_id_1,
                                                    global_id_2=global_id_2)
        except Conversation.DoesNotExist:
            try:
                conversation = Conversation.objects.get(global_id_1=global_id_2,
                                                        global_id_2=global_id_1)
            except Conversation.DoesNotExist:
                return HttpResponseBadRequest("There is no conversation " +
                                              "between these two users.")

        params['conversation'] = conversation

    if "date" in request.GET:
        try:
            dt = datetime.datetime.strptime(request.GET['date'], "%Y-%m-%d")
        except ValueError:
            return HttpResponseBadRequest("Invalid 'date' parameter value.")
        params['date'] = dt.date()

    if "tpp" in request.GET:
        try:
            params['tpp'] = int(request.GET['tpp'])
        except ValueError:
            return HttpResponseBadRequest("Invalid 'tpp' parameter value.")
    else:
        params['tpp'] = 20

    if "page" in request.GET:
        try:
            params['page'] = int(request.GET['page'])
        except ValueError:
            return HttpResponseBadRequest("Invalid 'page' parameter value.")
    else:
        params['page'] = 0

    # Get the user's profile, and check the HMAC authentication details.

    try:
        profile = Profile.objects.get(global_id=params['global_id'])
    except Profile.DoesNotExist:
        return HttpResponseBadRequest("There is no profile for that global ID")

    if not utils.check_hmac_authentication(request, profile.account_secret):
        return HttpResponseForbidden()

    # Get the user's Account record.  If it doesn't exist, create one.

    try:
        account = Account.objects.get(type=Account.TYPE_USER,
                                      global_id=params['global_id'])
    except Account.DoesNotExist:
        account = Account()
        account.type             = Account.TYPE_USER
        account.global_id        = params['global_id']
        account.balance_in_drops = 0
        account.save()

    print account.global_id, repr(params)

    # Calculate the information to return, based on the value of the "get"
    # parameter.

    if params['return'] == "balance":
        response = {'balance' : account.balance_in_drops}
    elif params['return'] == "transactions":
        response = _get_transactions(account, params)
    elif params['return'] == "totals" and params['group'] == "type":
        response = _get_totals_by_type(account, params)
    elif params['return'] == "totals" and params['group'] == "conversation":
        response = _get_totals_by_conversation(account, params)
    elif params['return'] == "totals" and params['group'] == "date":
        response = _get_totals_by_date(account, params)
    else:
        return HttpResponseBadRequest("Should never happen...")

    # Finally, return the response back to the caller.

    return HttpResponse(json.dumps(response),
                        mimetype="application/json")

#############################################################################
#                                                                           #
#                    P R I V A T E   D E F I N I T I O N S                  #
#                                                                           #
#############################################################################

def _legacy_account_GET(request):
    """ Legacy version of the "GET /account" endpoint.
    """
    if not utils.has_hmac_headers(request):
        return HttpResponseForbidden()

    # Get the request parameters.

    if "global_id" in request.GET:
        global_id_param = request.GET['global_id']
    else:
        return HttpResponseBadRequest("Missing 'global_id' parameter.")

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

    response = {'account': {}}

    # Get the transaction totals for this account.

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

#############################################################################

def _get_transactions(account, params):
    """ Return a list of transactions back to the caller.

        'account' is the Account record for the currently signed-in user, and
        'params' is a dictionary with at least the following entries:

            'type'

                If specified, this will be a string indicating the type of
                transactions to include in the results.  The following type
                values are currently supported:

                    "charges_paid"
                    "charges_received"
                    "deposits"
                    "withdrawals"
                    "adjustments_paid"
                    "adjustments_received"

                If no 'type' value is specified, all types of transactions will
                be included in the results.

            'conversation'

                If specified, this will be a Conversation object.  Only those
                transactions related to messages within that conversation will
                be included in the results.

            'date'

                If specified, this should be a datetime.date object.  Only
                transactions made on that date will be included in the results.

            'tpp'

                The maximum number of transactions to return per request.

            'page'

                The page number of transactions to return.

        Upon completion, we return a dictionary that looks like the following:

            {'transactions' : [...]}

        The 'transactions' entry will be a list of matching transactions as
        requested by the caller.
    """
    query = _build_success_query()
    query = query & _build_type_query(account, params)

    if "conversation" in params:
        query = query & _build_conversation_query(params['conversation'])

    if "date" in params:
        query = query & _build_date_query(date)

    results = Transaction.objects.filter(query).order_by("-timestamp")

    first = params['page'] * params['tpp']
    last  = (params['page']+1) * params['tpp']

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

        if transaction.message != None:
            trans['message_hash'] = transaction.message.hash

        transactions.append(trans)

    return {'transactions' : transactions}

#############################################################################

def _get_totals_by_type(account, params):
    """ Return a summary of matching transactions, grouped by type.

        'account' is the Account record for the currently signed-in user, and
        'params' is a dictionary with at least the following entries:

            'type'

                If specified, this will be a string indicating the type of
                transactions to include in the results.  The following type
                values are currently supported:

                    "charges_paid"
                    "charges_received"
                    "deposits"
                    "withdrawals"
                    "adjustments_paid"
                    "adjustments_received"

                If no 'type' value is specified, all types of transactions will
                be included in the results.

            'conversation'

                If specified, this will be a Conversation object.  Only those
                transactions related to messages within that conversation will
                be included in the results.

            'date'

                If specified, this should be a datetime.date object.  Only
                transactions made on that date will be included in the results.

        Upon completion, we return a dictionary that looks like the following:

            {'charges_paid'         : 999,
             'charges_received'     : 999,
             'deposits'             : 999,
             'withdrawals'          : 999,
             'adjustments_paid'     : 999,
             'adjustments_received' : 999}

        Each dictionary entry is the total value of the given type of
        transaction, in drops.  Note that a dictionary entry will only be
        present if there is at least one transaction of that type.
    """
    query = _build_success_query()
    query = query & _build_type_query(account, params)

    if "conversation" in params:
        query = query & _build_conversation_query(params['conversation'])

    if "date" in params:
        query = query & _build_date_query(date)

    transactions = Transaction.objects.filter(query)

    types = []

    # Calculate the charges paid.

    matches = transactions.filter(type__in=[Transaction.TYPE_SYSTEM_CHARGE,
                                            Transaction.TYPE_RECIPIENT_CHARGE],
                                  debit_account=account)
    total = matches.aggregate(total=Sum('amount_in_drops'))['total']

    if total != None:
        types.append({'type'  : 'charges_paid',
                      'total' : total})

    # Calculate the charges received.

    matches = transactions.filter(type=Transaction.TYPE_RECIPIENT_CHARGE,
                                  credit_account=account)
    total = matches.aggregate(total=Sum('amount_in_drops'))['total']

    if total != None:
        types.append({'type'  : 'charges_received',
                      'total' : total})

    # Calculate the deposits.

    matches = transactions.filter(type=Transaction.TYPE_DEPOSIT,
                                  credit_account=account)
    total = matches.aggregate(total=Sum('amount_in_drops'))['total']

    if total != None:
        types.append({'type'  : 'deposits',
                      'total' : total})

    # Calculate the withdrawals.

    matches = transactions.filter(type=Transaction.TYPE_WITHDRAWAL,
                                  debit_account=account)
    total = matches.aggregate(total=Sum('amount_in_drops'))['total']

    if total != None:
        types.append({'type'  : 'withdrawals',
                      'total' : total})

    # Calculate the adjustments paid.

    matches = transactions.filter(type=Transaction.TYPE_ADJUSTMENT,
                                  debit_account=account)
    total = matches.aggregate(total=Sum('amount_in_drops'))['total']

    if total != None:
        types.append({'type'  : 'adjustments_paid',
                      'total' : total})

    # Calculate the adjustments received.

    matches = transactions.filter(type=Transaction.TYPE_ADJUSTMENT,
                                  credit_account=account)
    total = matches.aggregate(total=Sum('amount_in_drops'))['total']

    if total != None:
        types.append({'type'  : 'adjustments_received',
                      'total' : total})

    return {'types' : types}

#############################################################################

def _get_totals_by_conversation(account, params):
    """ Return a summary of matching transactions, grouped by conversation.

        'account' is the Account record for the currently signed-in user, and
        'params' is a dictionary with at least the following entries:

            'type'

                If specified, this will be a string indicating the type of
                transactions to include in the results.  The following type
                values are currently supported:

                    "charges_paid"
                    "charges_received"
                    "deposits"
                    "withdrawals"
                    "adjustments_paid"
                    "adjustments_received"

                If no 'type' value is specified, all types of transactions will
                be included in the results.

            'conversation'

                If specified, this will be a Conversation object.  Only those
                transactions related to messages within that conversation will
                be included in the results.

            'date'

                If specified, this should be a datetime.date object.  Only
                transactions made on that date will be included in the results.

        Upon completion, we return a dictionary which looks like the following:

            {'john_smith'    : 999,
             'pete_mckenzie' : 999,
             ...
            }

        Each dictionary enty maps the global ID of the other party in the
        conversation to the total value of the matching transactions for that
        conversation, in drops.
    """
    query = _build_success_query()
    query = query & _build_type_query(account, params)

    if "conversation" in params:
        query = query & _build_conversation_query(params['conversation'])

    if "date" in params:
        query = query & _build_date_query(date)

    transactions = Transaction.objects.filter(query)

    results = transactions.values('message__conversation').annotate(
                                                total=Sum('amount_in_drops'))

    conversations = []
    for entry in results:
        total           = entry['total']
        conversation_id = entry['message__conversation']

        if conversation_id != None:
            try:
                conversation = Conversation.objects.get(id=conversation_id)
            except Conversation.DoesNotExist:
                continue # Should never happen.

        if conversation.global_id_1 == account.global_id:
            other_global_id = conversation.global_id_2
        elif conversation.global_id_2 == account.global_id:
            other_global_id = conversation.global_id_1
        else:
            continue # Should never happen.

        try:
            other_profile = Profile.objects.get(global_id=other_global_id)
        except Profile.DoesNotExist:
            other_profile = None

        other_name = None # initially.
        if other_profile != None and other_profile.name_visible:
            other_name = other_profile.name

        if other_name != None:
            sort_key = other_name
        else:
            sort_key = other_global_id

        conversations.append({'global_id' : other_global_id,
                              'name'      : other_name,
                              'total'     : total,
                              'sort_key'  : sort_key})

    conversations.sort(key=operator.itemgetter("sort_key"))

    for entry in conversations:
        del entry['sort_key']

    return {'conversations' : conversations}

#############################################################################

def _get_totals_by_date(account, params):
    """ Return a summary of matching transactions, grouped by date.

        'account' is the Account record for the currently signed-in user, and
        'params' is a dictionary with at least the following entries:

            'type'

                If specified, this will be a string indicating the type of
                transactions to include in the results.  The following type
                values are currently supported:

                    "charges_paid"
                    "charges_received"
                    "deposits"
                    "withdrawals"
                    "adjustments_paid"
                    "adjustments_received"

                If no 'type' value is specified, all types of transactions will
                be included in the results.

            'conversation'

                If specified, this will be a Conversation object.  Only those
                transactions related to messages within that conversation will
                be included in the results.

            'date'

                If specified, this should be a datetime.date object.  Only
                transactions made on that date will be included in the results.

        Upon completion, we return a dictionary which looks like the following:

            {'2015-01-06' : 999,
             '2015-01-07' : 999,
             ...
            }

        Each dictionary entry maps a date (in "YYYY-MM-DD" format) to the total
        value of the matching transactions for that day, in drops.
    """
    # Build the queryset of matching transactions.

    query = _build_success_query()
    query = query & _build_type_query(account, params)

    if "conversation" in params:
        query = query & _build_conversation_query(params['conversation'])

    if "date" in params:
        query = query & _build_date_query(date)

    transactions = Transaction.objects.filter(query)

    # If there are no matching transactions, return an empty dictionary.  This
    # avoids problems with calculating the minimum and maximum date based on an
    # empty list of transactions.

    if transactions.count() == 0:
        return {'dates' : []}

    # Find the minimum and maximum dates for these transactions.

    min_date = transactions.aggregate(min=Min('timestamp'))['min'].date()
    max_date = transactions.aggregate(max=Max('timestamp'))['max'].date()

    # Calculate the total for each day in turn.

    dates = []
    cur_date = min_date
    while cur_date <= max_date:
        sDate = cur_date.strftime("%Y-%m-%d")

        matches = transactions.filter(timestamp__year=date.year,
                                      timestamp__month=date.month,
                                      timestamp__day=date.day)
        total = matches.aggregate(tot=Sum('amount_in_drops'))['tot']

        if total != None:
            dates.append({'date'  : sDate,
                          'total' : total})

        cur_date = cur_date + datetime.timedelta(days=1)

    return {'dates' : dates}

#############################################################################

def _build_success_query():
    """ Return a Django "Q" object that returns only successful transactions.
    """
    return Q(status=Transaction.STATUS_SUCCESS)

#############################################################################

def _build_type_query(account, params):
    """ Build a Django database query to return transactions of the given type.

        We return a Django "Q" object that encapsulates a query against the
        Transaction table to return only those transactions which match the
        transaction type and account parameters.

        Note that this works even if no transaction type has been specified; in
        this case, all transactions are included in the query.
    """
    if params.get("type") == None:
        return Q(debit_account=account) | Q(credit_account=account)
    elif params.get("type") == "charges_paid":
        return (Q(type__in=[Transaction.TYPE_SYSTEM_CHARGE,
                            Transaction.TYPE_RECIPIENT_CHARGE]) &
                Q(debit_account=account))
    elif params.get("type") == "charges_received":
        return (Q(type=Transaction.TYPE_RECIPIENT_CHARGE) &
                Q(credit_account=account))
    elif params.get("type") == "deposits":
        return (Q(type=Transaction.TYPE_DEPOSIT) &
                Q(credit_account=account))
    elif params.get("type") == "withdrawals":
        return (Q(type=Transaction.TYPE_WITHDRAWAL) &
                Q(debit_account=account))
    elif params.get("type") == "adjustments_paid":
        return (Q(type=Transaction.TYPE_ADJUSTMENT) &
                Q(debit_account=account))
    elif params.get("type") == "adjustments_received":
        return (Q(type=Transaction.TYPE_ADJUSTMENT) &
                Q(credit_account=account))
    else:
        raise RuntimeError("Should never happen")

#############################################################################

def _build_conversation_query(conversation):
    """ Build a query to return transactions associated with a conversation.

        We return a Django "Q" object which only returns those transactions
        associated with the specified conversation object.
    """
    return Q(message__conversation=conversation)

#############################################################################

def _build_date_query(date):
    """ Build a query to return transactions with a given date.

        We return a Django "Q" object which only returns those transctions
        generated on the given datetime.date value.
    """
    return Q(timestamp__year=date.year,
             timestamp__month=date.month,
             timestamp__day=date.day)

