#!/usr/bin/env python

import webapp2
import json
import os

import config

import libs
import jwt

from google.appengine.api import users
from model.model import UserData

from util.json_serializer import JsonSerializer

ALLOWED_APP_IDS = ['localhosters-api']

ALLOW_ORIGIN_HEADER = 'Access-Control-Allow-Origin'
ALLOW_HEADERS_HEADER = 'Access-Control-Allow-Headers'
ALLOW_METHODS_HEADER = 'Access-Control-Allow-Methods'
CONTENT_TYPE_HEADER = 'Content-Type'
AUTHORIZATION_HEADER = 'Authorization'

BEARER_TOKEN_TYPE = 'Bearer'
JSON_CONTENT_TYPE = 'application/json'
ALLOWED_HEADERS = 'Authorization, Origin, X-Requested-With,' \
                  'Content-Type, Accept'

CONTENT_TYPE_JSON = 'application/json'

API_ERROR = 'api_error'
VALIDATION_ERROR = 'validation_error'

BODY_EMPTY = 'empty_body'

INVALID_FIELD = VALIDATION_ERROR + '.invalid_field'
MANDATORY_FIELD = VALIDATION_ERROR + '.mandatory_field'
FIELD_TOO_LONG = VALIDATION_ERROR + '.field_too_long'

ONE_OF_2 = 'Either %s or %s has to be specified'
ONE_OF_3 = 'Either %s, %s or %s has to be specified'

NOT_AUTHORIZED = 'Not authorized'

ERRORS = 'errors'
MESSAGE = 'message'


def login_required(handler):
    """Require that a user be logged in to access the resource."""
    def check_login(self, *args, **kwargs):

        subject_id = None
        provider = None

        if AUTHORIZATION_HEADER in self.headers:
            bearer_token = self.headers[AUTHORIZATION_HEADER]

            try:
                jwt_token = bearer_token.split(BEARER_TOKEN_TYPE + ' ')[1]
                payload = jwt.decode(jwt_token, config.jwt_secret,
                                     audience=config.jwt_audience,
                                     leeway=10)
                subject_id = payload['sub']
                provider = payload['provider']

            except jwt.DecodeError:
                # Secret is wrong
                pass

            except IndexError:
                # Formatting is wrong
                pass

            except (jwt.InvalidTokenError, jwt.ExpiredSignatureError,
                    jwt.InvalidAudienceError):
                # Re-login
                pass

        if subject_id is not None and provider is not None:

            user_model = UserData.query(
                UserData.subject_id == subject_id,
                UserData.provider == provider
            ).get()

            if user_model is not None:
                self.current_user = user_model
                return handler(self, *args, **kwargs)

        # Unauthorized if nothing matches
        return handler(self, *args, **kwargs)
        # TODO Include Auth!
        # self.respond(401)

    return check_login


class BaseHandler(webapp2.RequestHandler):

    _post_mandatory_fields = ()
    _get_mandatory_fields = ()

    def __init__(self, request=None, response=None,
                 requires_authentication=False):

        super(BaseHandler, self).__init__(request, response)

        self.read_request()
        self.setup_response()
        self.current_user = None

    def dispatch(self):
        if(self.validate()):
            super(BaseHandler, self).dispatch()

    def read_request(self):

        self.request.path_info_pop()
        self.headers = self.request.headers
        self.inputBody = self.request.body

        if (CONTENT_TYPE_HEADER in self.headers and
                CONTENT_TYPE_JSON in self.headers.get(CONTENT_TYPE_HEADER)):

            if self.request.body:
                self.inputBody = json.loads(self.request.body)
            else:
                self.inputBody = dict()

    def setup_response(self):
        self.request.path_info_pop()
        self.headers = self.request.headers

        self.response.status = 404
        self.response.headers[CONTENT_TYPE_HEADER] = JSON_CONTENT_TYPE
        self.response.headers[ALLOW_METHODS_HEADER] = 'POST, PUT, DELETE, GET, OPTIONS'
        self.response.headers[ALLOW_ORIGIN_HEADER] = '*'

    def options(self, **args):
        self.response.headers[ALLOW_HEADERS_HEADER] = ALLOWED_HEADERS
        self.response.status = 204

    def respond(self, status_code, body=None, headers=None):
        self.response.status = status_code
        self.response.write(json.dumps(body, cls=JsonSerializer)
                            if body is not None else '{}')

        if headers is not None:
            self.response.headers.extend(headers)

    def validate(self):

        no_evaluate = self.request.route.handler_method is not None
        if no_evaluate:
            return True

        fields = None
        body = None
        method_validation = None

        if self.request.method == 'GET':
            method_validation = self.validate_get
            fields = self._get_mandatory_fields
            body = self.request.GET

        elif self.request.method == 'POST':
            method_validation = self.validate_post
            fields = self._post_mandatory_fields
            body = self.inputBody

        else:
            return True

        field_success, error_fields = self.validate_fields(body, fields)
        method_success = False

        if not field_success:
            self.respond(422, {ERRORS: error_fields})

        else:
            method_success, errors = method_validation()
            if not method_success:
                self.respond(422, {ERRORS: errors})

        return field_success & method_success

    def validate_fields(self, body, mandatory_fields):

        error_fields = dict()

        for mandatory_field in mandatory_fields:
            if mandatory_field not in body:
                error_fields[mandatory_field] = MANDATORY_FIELD

        success = len(error_fields) == 0
        return success, error_fields

    def validate_get(self):
        return True, None

    def validate_post(self):
        return True, None
