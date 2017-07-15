#!/usr/bin/env python

import time

import base
import config

from util import open_id

from model.model import UserData

GOOGLE_ACCOUNTS_ISS = ['accounts.google.com', 'https://accounts.google.com']

PROVIDER_FIELD = 'provider'
ID_TOKEN_FIELD = 'id_token'
ACCESS_TOKEN_FIELD = 'access_token'
EMAIL_FIELD = 'email'

INVALID_TOKEN = base.VALIDATION_ERROR + '.invalid_token'
PROVIDER_NOT_SPECIFIED = base.VALIDATION_ERROR + '.provider_not_specified'
EMAIL_TAKEN = base.VALIDATION_ERROR + '.email_taken'
UNAUTHORIZED_EMAIL = base.API_ERROR + '.email_not_authorized'


class AuthenticateController(base.BaseHandler):

    _post_mandatory_fields = (
        PROVIDER_FIELD, ID_TOKEN_FIELD, ACCESS_TOKEN_FIELD)

    def process_provider_token(self, provider, id_token):

        try:
            idinfo = open_id.verify_id_token(id_token, config.client_id)
        except:
            return None

        if idinfo.get('aud') not in config.audiences:
            return None

        if idinfo.get('iss') not in GOOGLE_ACCOUNTS_ISS:
            return None

        if int(idinfo.get('exp')) < int(time.time()):
            return None

        return idinfo

    def post(self):

        id_token = self.inputBody.get(ID_TOKEN_FIELD)
        access_token = self.inputBody.get(ACCESS_TOKEN_FIELD)
        provider = self.inputBody.get(PROVIDER_FIELD)

        result = self.process_provider_token(provider, id_token)

        if result is not None:

            email = result.get('email')
            subject_id = result.get('sub')
            user = UserData.query(
                UserData.subject_id == subject_id,
                UserData.provider == provider
            ).get()

            if user is None:
                user = self._create_user(
                    subject_id, email, provider, access_token)

            self.respond(200, user.me())

        else:
            self.respond(422, {base.ERRORS: {EMAIL_FIELD: INVALID_TOKEN}})

    @staticmethod
    def _create_user(subject_id, email, provider, access_token):

        # Fetch user info
        user_data = open_id.get_profile_info(access_token)

        return UserData.create_user(subject_id, email, provider, user_data)
