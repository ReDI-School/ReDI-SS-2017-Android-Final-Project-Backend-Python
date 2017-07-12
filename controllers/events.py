#!/usr/bin/env python

from google.appengine.ext import ndb

import base
from base import login_required

from model.model import Event, Invite, EventUserStatus
from datetime import datetime

NAME_FIELD = 'name'
PLACE_FIELD = 'place'
TIME_FIELD = 'time'

LOCATION_FIELD = 'location'
LATITUDE_FIELD = 'lat'
LONGITUDE_FIELD = 'lon'
STATUS_FIELD = 'status'

DATE_FORMAT = '%Y-%m-%dT%H:%MZ'


class EventController(base.BaseHandler):

    _post_mandatory_fields = (NAME_FIELD, PLACE_FIELD, TIME_FIELD)

    @login_required
    def get(self):

        # Fetch events that user created
        user_events = Event.query().filter(
            Event.owner == self.current_user.key).fetch()

        # Fetch events that user is invited to
        my_invites = Invite.query(
            ancestor=self.current_user.key).filter(Invite.state == 'accepted')

        event_keys = [invite.event for invite in my_invites]
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

        event = Event(owner=self.current_user.key,
                      name=name, place=place, time=time)
        event.put()
        self.respond(201, event)

    def validate_post(self):

        errors = dict()

        time_str = self.inputBody.get(TIME_FIELD)
        try:
            datetime.strptime(time_str, DATE_FORMAT)
        except ValueError:
            errors[TIME_FIELD] = 'Date time format must be %s' % DATE_FORMAT

        return len(errors) == 0, errors


class SingleEventController(base.BaseHandler):

    @login_required
    def get(self, event_id_str):

        event = Event.get_by_id(int(event_id_str))
        if event is not None and event.user_is_allowed(self.current_user):

            # Fetch attendees statuses
            attendees_status = EventUserStatus.query(
                ancestor=event.key).fetch()

            event_dict = event.to_dict()
            event_dict['attendees_status'] = [
                status.to_dict() for status in attendees_status]

            self.respond(200, event_dict)

        else:
            self.respond(404)

    @login_required
    def post(self, event_id_str):
        event = Event.get_by_id(int(event_id_str))
        if event is not None and event.user_is_allowed(self.current_user):

            if LOCATION_FIELD in self.inputBody:
                location_body = self.inputBody.get(LOCATION_FIELD)
                location = ndb.GeoPt(lat=location_body[LATITUDE_FIELD],
                                     lon=location_body[LONGITUDE_FIELD])
            else:
                location = None

            EventUserStatus.create_or_update(
                event.key, self.current_user.key,
                self.inputBody.get(STATUS_FIELD), location)

            self.respond(204)

        else:
            self.respond(404)

    @login_required
    def delete(self, event_id_str):
        event = Event.get_by_id(int(event_id_str))
        if event is not None and event.user_is_owner(self.current_user):
            event.key.delete()

        self.respond(204)

    def validate_post(self):

        errors = dict()

        if LOCATION_FIELD in self.inputBody:
            location_body = self.inputBody[LOCATION_FIELD]
            if (LATITUDE_FIELD not in location_body or
                    LONGITUDE_FIELD not in location_body):
                errors[LOCATION_FIELD] = (
                    'Location needs to include values for both lat and lon.')

        elif STATUS_FIELD not in self.inputBody:
            errors[base.VALIDATION_ERROR] = (
                'One of {} or {} needs to be included.'.format(
                    LOCATION_FIELD, STATUS_FIELD))

        return len(errors) == 0, errors
