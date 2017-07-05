#!/usr/bin/env python

from google.appengine.ext import ndb

import base
from base import login_required

from model.model import Event, Invite, UserData

RECIPIENT_ID_FIELD = 'name'
EVENT_ID_FIELD = 'place'


class InviteController(base.BaseHandler):

    _post_mandatory_fields = (RECIPIENT_ID_FIELD, EVENT_ID_FIELD)

    @login_required
    def get(self):

        # TODO When logging in is there
        # user_id = self.user_id
        user_id = 1

        pending_invites = Invite.query(
            ancestor=ndb.Key(UserData, user_id),
            Invite.state=='pending'
        ).fetch()

        self.respond(200, pending_invites)

    @login_required
    def post(self):

        recipient = UserData.get_by_id(self.inputBody.get(RECIPIENT_ID_FIELD))
        event = Event.get_by_id(self.inputBody.get(EVENT_ID_FIELD))
        invite = Invite(ancestor=recipient.key, event=event.key,
                        sender=ndb.Key(UserData, 1), )
        invite.put()
        return invite

    def validate_post(self):

        errors = dict()

        recipient_id = self.inputBody.get(RECIPIENT_ID_FIELD)
        recipient = UserData.get_by_id(recipient_id)
        if recipient is None:
            errors[RECIPIENT_ID_FIELD] = base.VALIDATION_ERROR + ".not_found"

        event_id = self.inputBody.get(EVENT_ID_FIELD)
        event = Event.get_by_id(event_id)
        if event is None:
            errors[EVENT_ID_FIELD] = base.VALIDATION_ERROR + ".not_found"

        return len(errors) == 0, errors


class SingleInviteController(base.BaseHandler):

    VALID_ACTIONS = {'accept', 'reject'}

    @login_required
    def get(self, invite_id_str):
        invite = Invite.get_by_id(invite_id_str)
        if invite:
            self.respond(200, invite)
        else:
            self.respond(404)

    @login_required
    def post(self, invite_id_str, invite_action):

        if invite_action not in VALID_ACTIONS:
            self.respond(
                422, 'Action must be one of ' % ' or '.join(VALID_ACTIONS))
            return

        invite = Invite.get_by_id(invite_id_str)
        if not invite:
            self.respond(404)
            return

        if invite_action == 'accept':
            invite.state = 'accepted'

        if invite_action == 'reject':
            invite.state = 'rejected'

        invite.put()
        return invite

    @login_required
    def delete(self, invite_id_str):
        ndb.Key(Invite, invite_id_str).delete()
        self.respond(204)
