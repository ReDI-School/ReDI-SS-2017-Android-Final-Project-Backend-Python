#!/usr/bin/env python

import config

# Google's AppEngine modules:
import webapp2
from webapp2 import Route
from webapp2_extras import routes
from webapp2_extras.routes import DomainRoute

# Controllers and handlers
from controllers.sessions import AuthenticateController
from controllers.users import UserController, MeController
from controllers.events import EventController, SingleEventController
from controllers.invites import InviteController, SingleInviteController

# Requested URLs that are not listed here,
# will return 404

ROUTES = [
    DomainRoute(config.host, [

        # Sessions
        Route(r'/authenticate',
              handler=AuthenticateController, name='authenticate'),

        # Users
        routes.PathPrefixRoute(r'/users', [

            Route(r'', handler=UserController, name='users',
                  methods=['GET', 'OPTIONS']),

            Route(r'/me', handler=MeController, name='users',
                  methods=['GET', 'OPTIONS']),
        ]),

        # Events
        routes.PathPrefixRoute(r'/events', [

            Route(r'', handler=EventController, name='events',
                  methods=['GET', 'POST', 'OPTIONS']),

            routes.PathPrefixRoute(r'/<event_id_str:\d+>', [

                Route(r'', handler=SingleEventController,
                      name='events', methods=['GET', 'DELETE', 'OPTIONS']),

                Route(r'', handler=SingleEventController,
                      name='events', methods=['POST', 'OPTIONS']),
            ]),
        ]),

        # Invites
        routes.PathPrefixRoute(r'/invites', [

            Route(r'', handler=InviteController, name='invites',
                  methods=['GET', 'POST', 'OPTIONS']),

            routes.PathPrefixRoute(r'/<invite_id_str:\d+>', [

                Route(r'', handler=SingleInviteController,
                      name='invites', methods=['GET', 'DELETE', 'OPTIONS']),

                Route(r'/<invite_action:\w+>', handler=SingleInviteController,
                      name='invites', methods=['POST', 'OPTIONS'])
            ]),
        ]),
    ])
]
app = webapp2.WSGIApplication(ROUTES, debug=True)
