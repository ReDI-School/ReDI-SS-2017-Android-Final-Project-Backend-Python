#!/usr/bin/env python

from google.appengine.ext import ndb

import base
from base import login_required

from model.model import Event, Invite, UserData
from datetime import datetime

NAME_FIELD = 'name'
PLACE_FIELD = 'place'
TIME_FIELD = 'time'

DATE_FORMAT = '%Y-%m-%dT%H:%MZ'


class EventController(base.BaseHandler):

    _post_mandatory_fields = (NAME_FIELD, PLACE_FIELD, TIME_FIELD)

    @login_required
    def get(self):

        # TODO When logging in is there
        # user_id = self.user_id
        user_id = 1

        # Fetch events that user created
        user_events = Event.query(ancestor=ndb.Key(UserData, user_id)).fetch()

        # Fetch events that user is invited to
        my_invites = Invite.query(ancestor=ndb.Key(UserData, user_id),
                                  Invite.state=='accepted')

        event_keys = []
        for invite in my_invites:
            event_keys.append(invite.event)

        events_user_is_invited_to = ndb.get_multi(event_keys)

        # Merge results and respond
        user_events.extend(events_user_is_invited_to)
        self.respond(200, user_events)

    @login_required
    def post(self):

        name = self.inputBody.get(NAME_FIELD)
        place = self.inputBody.get(PLACE_FIELD)
        time_str = self.inputBody.get(TIME_FIELD)
        time = datetime.strptime(time_str, DATE_FORMAT)

        event = Event(ancestor=ndb.Key(UserData, 1),
                      name=name, place=place, time=time)
        event.put()
        return event

    def validate_post(self):

        errors = dict()

        time_str = self.inputBody.get(TIME_FIELD)
        try:
            datetime.strptime(time_str, DATE_FORMAT)
        except ValueError:
            errors[TIME_FIELD] = 'Date time format must be ' % DATE_FORMAT

        return len(errors) == 0, errors


class SingleEventController(base.BaseHandler):

    @login_required
    def get(self, event_id_str):
        event = Event.get_by_id(event_id_str)
        if event:
            self.respond(200, event)
        else:
            self.respond(404)

    @login_required
    def delete(self, event_id_str):
        ndb.Key(Event, event_id_str).delete()
        self.respond(204)
