""" mmServer.shared.lib.dbHelpers

    This module define various helper functions and classes for working with
    the database.
"""
import logging

from django.conf import settings
from django.db   import transaction, connection

#############################################################################

logger = logging.getLogger(__name__)

#############################################################################

class exclusive_access():
    """ A context manager that provides exclusive access to a database table.

        This context manager, which only works with PostgreSQL, applies an
        "ACCESS EXCLUSIVE" lock to one or more Django models and starts an
        atomic transaction on entry, and then releases the transaction on exit.
        This has the effect of applying an exlusive lock on the given database
        table(s), so that nobody else can access those tables (even for
        reading) while the given code is being executed.  Note that either
        committing or rolling back the transaction (which happens when leaving
        the context) will automatically release the exclusive lock.
    """
    def __init__(self, *models):
        """ Standard initialiser.

            'models' is a list of the Django model(s) that we want an exclusive
            table lock for.
        """
        self._models      = models
        self._transaction = transaction.atomic()


    def __enter__(self):
        """ Enter our context.
        """
        self._transaction.__enter__()

        if "postgresql" in settings.DATABASES['default']['ENGINE']:
            cursor = connection.cursor()
            for model in self._models:
                cursor.execute("LOCK TABLE %s IN ACCESS EXCLUSIVE MODE" %
                               model._meta.db_table)


    def __exit__(self, exc_type, exc_value, exc_traceback):
        """ Leave our context.
        """
        self._transaction.__exit__(exc_type, exc_value, exc_traceback)

