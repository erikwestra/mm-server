""" mmServer.api.urls

    This is the URL configuration for the mmServer.api application.
"""
from django.conf.urls import *

#############################################################################

urlpatterns = patterns('mmServer.api.views',
    url(r'^profile/(?P<global_id>.*)$', 'profile'),
    # more to come...
)

