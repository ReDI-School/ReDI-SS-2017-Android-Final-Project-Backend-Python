#!/usr/bin/env python

import config

from datetime import datetime
from datetime import timedelta

from google.appengine.ext import ndb

import jwt

from base import BaseModel

PROVIDER_GOOGLE = 'google'
PROVIDER_FACEBOOK = 'facebook'


class UserData(BaseModel):

    _serialized_fields = ['created', 'email', 'name',
                          'username', 'picture', 'punctuality']

    email = ndb.StringProperty(required=True)
    name = ndb.StringProperty(required=True)
    username = ndb.StringProperty()
    picture = ndb.StringProperty()
    punctuality = ndb.FloatProperty()
    subject_id = ndb.StringProperty(required=True)
    provider = ndb.StringProperty(choices=[
        PROVIDER_GOOGLE, PROVIDER_FACEBOOK], required=True)
    type = ndb.StringProperty(choices=['user', 'admin'], default='user')

    @classmethod
    def create_user(cls, subject_id, email, provider, user_data):

        user = UserData(
            subject_id=subject_id, email=email, provider=provider, type='user')

        # Add provider specific user data
        if user_data is not None:

            if provider == PROVIDER_GOOGLE:
                user.name = user_data.get('given_name')
                user.picture = user_data.get('picture')

            elif provider == PROVIDER_FACEBOOK:
                pass

            else:
                raise ValueError('Provider is unknown: ' + provider)

        user.put()
        return user

    def me(self):

        user_dict = self.to_dict()

        jwt_payload = jwt.encode(
            {
                'sub': self.subject_id,
                'provider': self.provider,
                'exp': datetime.utcnow() + timedelta(days=365),
                'aud': config.jwt_audience
            },
            config.jwt_secret)

        user_dict['token'] = jwt_payload
        return user_dict


class Event(BaseModel):

    _serialized_fields = ['created', 'place', 'name',
                          'time', 'attendees']

    # owner = Parent entity and thus not included in the model
    place = ndb.StringProperty(required=True)
    name = ndb.StringProperty(required=True)
    time = ndb.DateTimeProperty(required=True)


class Invite(BaseModel):

    _serialized_fields = ['created', 'modified', 'sender_id']

    # recipient = Parent entity and thus not included in the model
    sender = ndb.KeyProperty(required=True)
    event = ndb.KeyProperty(required=True)
    state = ndb.StringProperty(choices=['pending', 'accepted', 'rejected'],
                               default='pending')


class EventUserStatus(BaseModel):

    _serialized_fields = ['modified', 'user_id', 'location', 'status']

    # event = Parent entity and thus not included in the model
    user = ndb.KeyProperty(required=True)
    last_location = ndb.GeoPtProperty()
    status = ndb.TextProperty()
