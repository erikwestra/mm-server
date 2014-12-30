""" mmServer.api.urls

    This is the URL configuration for the mmServer.api application.
"""
from django.conf.urls import *

#############################################################################

urlpatterns = patterns('',
    url(r'^profile/(?P<global_id>.*)$',  'mmServer.api.views.profile.endpoint'),
    url(r'^picture$',                    'mmServer.api.views.picture.endpoint'),
    url(r'^picture/(?P<picture_id>.*)$', 'mmServer.api.views.picture.endpoint'),
    # more to come...
)

