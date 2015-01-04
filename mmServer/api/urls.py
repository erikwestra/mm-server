""" mmServer.api.urls

    This is the URL configuration for the mmServer.api application.
"""
from django.conf.urls import *

#############################################################################

urlpatterns = patterns('',
    url(r'^profiles$', 'mmServer.api.views.profiles.endpoint'),

    url(r'^profile/(?P<global_id>.*)$', 'mmServer.api.views.profile.endpoint'),

    url(r'^picture$',                    'mmServer.api.views.picture.endpoint'),
    url(r'^picture/(?P<picture_id>.*)$', 'mmServer.api.views.picture.endpoint'),

    url(r'^conversations/(?P<global_id>.*)$',
                                   'mmServer.api.views.conversations.endpoint'),

    url(r'^conversation$', 'mmServer.api.views.conversation.endpoint'),
)

