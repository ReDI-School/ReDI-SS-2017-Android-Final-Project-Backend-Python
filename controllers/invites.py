#!/usr/bin/env python

from google.appengine.ext import ndb

import base
from base import login_required

from model.model import Event, Invite, UserData

RECIPIENT_ID_FIELD = 'recipient_id'
RECIPIENT_EMAIL_FIELD = 'recipient_email'
EVENT_ID_FIELD = 'event_id'


class InviteController(base.BaseHandler):

    _post_mandatory_fields = (EVENT_ID_FIELD,)

    @login_required
    def get(self):

        pending_invites = Invite.query(
            ancestor=self.current_user.key).filter(Invite.state == 'pending'
        ).fetch()

        self.respond(200, pending_invites)

    @login_required
    def post(self):

        if RECIPIENT_ID_FIELD in self.inputBody:
            recipient = UserData.get_by_id(
                self.inputBody.get(RECIPIENT_ID_FIELD))

        elif RECIPIENT_EMAIL_FIELD in self.inputBody:
            recipient = UserData.get_by_email(
                self.inputBody.get(RECIPIENT_EMAIL_FIELD))

        event = Event.get_by_id(int(self.inputBody.get(EVENT_ID_FIELD)))

        current_user = self.current_user
        if event.user_is_allowed(current_user):

            invite = Invite.query(ancestor=recipient.key).filter(
                Invite.event == event.key).get()
            if not invite:

                invite = Invite(parent=recipient.key, event=event.key,
                                sender=current_user.key)
                invite.put()

            self.respond(201, invite)

        else:
            self.respond(404)

    def validate_post(self):

        errors = dict()

        recipient = None
        if RECIPIENT_ID_FIELD in self.inputBody:
            recipient_id = self.inputBody.get(RECIPIENT_ID_FIELD)
            recipient = UserData.get_by_id(recipient_id)

        elif RECIPIENT_EMAIL_FIELD in self.inputBody:
            recipient_email = self.inputBody.get(RECIPIENT_EMAIL_FIELD)
            recipient = UserData.get_by_email(recipient_email)

        else:
            errors[base.VALIDATION_ERROR] = (
                'Either a recipient_id or recipient_email needs to be included'
                ' to refer to a user.')

        if recipient is None:
            errors[RECIPIENT_ID_FIELD] = base.VALIDATION_ERROR + ".not_found"

        event_id = self.inputBody.get(EVENT_ID_FIELD)
        event = Event.get_by_id(int(event_id))
        if event is None:
            errors[EVENT_ID_FIELD] = base.VALIDATION_ERROR + ".not_found"

        return len(errors) == 0, errors


class SingleInviteController(base.BaseHandler):

    VALID_ACTIONS = {'accept', 'reject'}

    @login_required
    def get(self, invite_id_str):

        recipient_id = self.request.get(
            RECIPIENT_ID_FIELD, self.current_user.key.id())
        invite = Invite.get_by_id(int(recipient_id), int(invite_id_str))
        if invite:
            self.respond(200, invite)
        else:
            self.respond(404)

    @login_required
    def post(self, invite_id_str, invite_action):

        if invite_action not in self.VALID_ACTIONS:
            self.respond(
                422,
                'Action must be one of %s' % ', '.join(self.VALID_ACTIONS))
            return

        current_user_id = self.current_user.key.id()
        invite = Invite.get_by_id(current_user_id, int(invite_id_str))
        if not invite:
            self.respond(404)
            return

        if invite_action == 'accept':
            invite.state = 'accepted'

        if invite_action == 'reject':
            invite.state = 'rejected'

        invite.put()
        self.respond(200, invite)

    @login_required
    def delete(self, invite_id_str):

        recipient_id = self.request.get(RECIPIENT_ID_FIELD)
        invite = Invite.get_by_id(int(recipient_id), int(invite_id_str))
        if invite and invite.user_is_sender(self.current_user):
            invite.key.delete()

        self.respond(204)
