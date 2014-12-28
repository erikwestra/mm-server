""" mmServer.urls

    This is the top-level URL configuration module for the mmServer system.
"""
from django.conf.urls import *

#############################################################################

# Include our API urls.

urlpatterns = patterns('',
    url(r'^api/', include("mmServer.api.urls")),
)

