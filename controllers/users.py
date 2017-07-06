#!/usr/bin/env python

from google.appengine.ext import ndb

import base
from base import login_required


class UserController(base.BaseHandler):

    @login_required
    def get(self):

        raw_ids = self.request.get_all('id[]', default_value=[])
        if len(raw_ids) > 0:

            ids = frozenset(map(int, raw_ids))
            keys = []

            for id in ids:
                keys.append(ndb.Key('UserData', id))

            results = ndb.get_multi(keys)
            self.respond(200, filter(None, results))

        else:
            self.respond(422, "This endpoint needs a list of ids")


class MeController(base.BaseHandler):

    @login_required
    def get(self):
        self.respond(200, self.current_user)
