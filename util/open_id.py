import json
import urllib

from google.appengine.api import urlfetch

from libs.oauth2client import client as client
from libs.oauth2client import _helpers
from libs.oauth2client import crypt
from libs.oauth2client.client import VerifyJwtTokenError

PROFILE_INFO_GOOGLE = 'google'


def verify_id_token(id_token, audience, http=None,
                    cert_uri=client.ID_TOKEN_VERIFICATION_CERTS):
    """Verifies a signed JWT id_token.

    This function is a copy of the one in oauth2client library, enabling
    support for App Engine. Using regular URL Fetch calls.

    Args:
        id_token: string, A Signed JWT.
        audience: string, The audience 'aud' that the token should be for.
        http: httplib2.Http, instance to use to make the HTTP request. Callers
              should supply an instance that has caching enabled.
        cert_uri: string, URI of the certificates in JSON format to
                  verify the JWT against.

    Returns:
        The deserialized JSON in the JWT.

    Raises:
        oauth2client.crypt.AppIdentityError: if the JWT fails to verify.
        CryptoUnavailableError: if no crypto library is available.
    """
    client._require_crypto_or_die()

    certs_request = urlfetch.fetch(cert_uri)
    if certs_request.status_code == 200:
        certs = json.loads(_helpers._from_bytes(certs_request.content))
        return crypt.verify_signed_jwt_with_certs(id_token, certs, audience)
    else:
        raise VerifyJwtTokenError('Status code: {0}'.format(certs_request.status_code))


def get_profile_info(id_token, access_token, provider=PROFILE_INFO_GOOGLE):

    params = {'id_token': id_token, 'access_token': access_token}
    response = urlfetch.fetch(
        url='https://www.googleapis.com/oauth2/v3/userinfo?%s' % urllib.urlencode(params),
        method=urlfetch.POST,
        headers={'Content-Type': 'application/json'})

    if response.status_code == 200:
        return json.loads(response.content)
    else:
        return None
