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
    def get_by_email(cls, email_address):
        return UserData.query(cls.email == email_address).get()

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

    _DEFAULT_EVENTS_BUCKET = ndb.Key('Bucket', 'default')
    _serialized_fields = ['created', 'place', 'name', 'time']

    owner = ndb.KeyProperty(required=True)
    place = ndb.StringProperty(required=True)
    name = ndb.StringProperty(required=True)
    time = ndb.DateTimeProperty(required=True)

    def __init__(self, *args, **kwds):
        super(Event, self).__init__(
            parent=self._DEFAULT_EVENTS_BUCKET, *args, **kwds)

    @classmethod
    def get_by_id(cls, event_id):
        return ndb.Key(
            flat=cls._DEFAULT_EVENTS_BUCKET.flat() + (cls, event_id)).get()

    @classmethod
    def query(cls):
        return super(Event, cls).query(ancestor=cls._DEFAULT_EVENTS_BUCKET)

    def user_is_owner(self, user):
        return self.owner == user.key

    def user_is_allowed(self, user):
        return (
            self.user_is_owner(user) or
            Invite.query(ancestor=user.key).filter(Invite.event == self.key))


class EventUserStatus(BaseModel):

    _serialized_fields = ['modified', 'user', 'last_location', 'status']

    # event = Parent entity and thus not included in the model
    user = ndb.KeyProperty(kind=UserData, required=True)
    last_location = ndb.GeoPtProperty()
    status = ndb.TextProperty()

    @classmethod
    def create_or_update(cls, event_key, user_key, status, location):

        current_user_status = cls.query(
            ancestor=event_key).filter(cls.user == user_key).get()

        if current_user_status is None:
            next_user_status = cls(
                parent=event_key, user=user_key, status=status,
                last_location=location)

        else:
            next_user_status = current_user_status
            if status is not None:
                next_user_status.status = status

            if location is not None:
                next_user_status.last_location = location

        next_user_status.put()


class Invite(BaseModel):

    _serialized_fields = ['created', 'modified', 'state']

    # recipient = Parent entity and thus not included in the model
    sender = ndb.KeyProperty(kind=UserData, required=True)
    event = ndb.KeyProperty(kind=Event, required=True)
    state = ndb.StringProperty(choices=['pending', 'accepted', 'rejected'],
                               default='pending')

    def to_dict(self):

        return (dict(
            super(Invite, self).to_dict().items() +
            {
                'sender_id': self.sender.id(),
                'recipient_id': self.key.parent().id(),
                'event_id': self.event
            }.items()))

    @classmethod
    def get_by_id(cls, recipient_id, invite_id):
        return ndb.Key(UserData, recipient_id, Invite, invite_id).get()

    def user_is_sender(self, user):
        return self.sender == user.key
