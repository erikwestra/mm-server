""" mmServer.api.urls

    This is the URL configuration for the mmServer.api application.
"""
from django.conf.urls import *

#############################################################################

urlpatterns = patterns('',
    url(r'^profiles$', 'mmServer.api.views.profiles.endpoint'),

    url(r'^profile/(?P<global_id>.*)$', 'mmServer.api.views.profile.endpoint'),

    url(r'^account$', 'mmServer.api.views.account.endpoint'),

    url(r'^transaction$', 'mmServer.api.views.transaction.endpoint'),

    url(r'^picture$',                    'mmServer.api.views.picture.endpoint'),
    url(r'^picture/(?P<picture_id>.*)$', 'mmServer.api.views.picture.endpoint'),

    url(r'^conversations/(?P<global_id>.*)$',
                                   'mmServer.api.views.conversations.endpoint'),

    url(r'^conversation$', 'mmServer.api.views.conversation.endpoint'),

    url(r'^messages$', 'mmServer.api.views.messages.endpoint'),

    url(r'^message$', 'mmServer.api.views.message.endpoint'),

    url(r'^changes$', 'mmServer.api.views.changes.endpoint'),
)

