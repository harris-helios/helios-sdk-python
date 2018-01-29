"""Manager for the authorization token required to access the Helios API."""
import json
import logging
import os

import requests

# Python 2 compatibility.
try:
    FileNotFoundError
except NameError:
    FileNotFoundError = IOError


class SessionManager(object):
    """Manages API tokens for authentication.

    Authentication credentials can be specified using the env input parameter,
    environment variables, or a .helios_auth file in your home directory.  See
    the official documentation for more authentication information.

    A session can be established and reused for multiple core API instances.

    .. code-block:: python

        import helios
        sess = helios.session.SessionManager()
        sess.start_session()
        alerts = helios.Alerts(session=sess)
        cameras = helios.Cameras(session=sess)

    If a session is not specified before hand, one will be initialized
    automatically.  This is less efficient because each core API instance
    will try to initialize a session.

    .. code-block:: python

        import helios
        alerts = helios.Alerts()
        cameras = helios.Cameras()

    """

    token_expiration_threshold = 60  # minutes

    _token_file = os.path.join(os.path.expanduser('~'), '.helios_token')
    _auth_file = os.path.join(os.path.expanduser('~'), '.helios_auth')
    _default_api_url = r'https://api.helios.earth/v1/'

    def __init__(self, env=None):
        """Initialize Helios Session.

        Args:
            env (dict): Dictionary containing HELIOS_KEY_ID,
                HELIOS_KEY_SECRET, and optionally, 'HELIOS_API_URL'. This will
                override any information in .helios_auth and environment
                variables.
        """
        # Initialize logger
        self.logger = logging.getLogger(__name__)

        # The token will be established with a call to the start_session method.
        self.token = None

        # Try to load essential authentication data from environment or file.
        if env:
            self.logger.info('Using custom env for session.')
            data = env
            # Delete token file so that custom env can be used.
            self._delete_token()
        elif 'HELIOS_KEY_ID' in os.environ and 'HELIOS_KEY_SECRET' in os.environ:
            self.logger.info('Using environment variables for session.')
            data = os.environ
        else:
            self.logger.info('Using .helios_auth file for session.')
            try:
                with open(self._auth_file, 'r') as auth_file:
                    data = json.load(auth_file)
            except (IOError, FileNotFoundError):
                raise Exception('No credentials could be found. Be sure to '
                                'set environment variables or setup a '
                                '.helios_auth file.')

        # Extract relevant authentication information from data.
        self._key_id = data['HELIOS_KEY_ID']
        self._key_secret = data['HELIOS_KEY_SECRET']
        try:
            self.api_url = data['HELIOS_API_URL']
        except KeyError:
            self.api_url = self._default_api_url

        self.token_url = self.api_url + '/oauth/token'

    def _delete_token(self):
        """Delete token file."""
        try:
            os.remove(self._token_file)
        except (WindowsError, FileNotFoundError):
            pass

    def _read_token_file(self):
        """Read token from file."""
        with open(self._token_file, 'r') as token_file:
            self.token = json.load(token_file)

    def _write_token_file(self):
        """Write token to file."""
        with open(self._token_file, 'w+') as token_file:
            json.dump(self.token, token_file)

    def get_token(self):
        """
        Gets a fresh token.

        The token will be acquired and then written to file for reuse. If the
        request fails over https, http will be used as a fallback.

        """
        try:
            data = {'grant_type': 'client_credentials'}
            auth = (self._key_id, self._key_secret)
            resp = requests.post(self.token_url, data=data, auth=auth,
                                 verify=True)
            resp.raise_for_status()
        except requests.exceptions.HTTPError:
            self.logger.warning('Getting token over https failed. Falling '
                                'back to http.')
            token_url_http = 'http' + self.token_url.split('https')[1]
            data = {'grant_type': 'client_credentials'}
            auth = (self._key_id, self._key_secret)
            resp = requests.post(token_url_http, data=data, auth=auth,
                                 verify=True)

        # If the token cannot be acquired, raise exception.
        resp.raise_for_status()

        token_request = resp.json()
        self.token = {'name': 'Authorization',
                      'value': 'Bearer ' + token_request['access_token']}

        self._write_token_file()

    def start_session(self):
        """
        Begin Helios session.

        This will establish and verify a token for the session.  If a token
        file exists the token will be read and verified.

        """
        # Check for saved token first. If it doesn't exist then get a token.
        try:
            self._read_token_file()
            if not self.verify_token():
                self.get_token()
        except (IOError, FileNotFoundError):
            self.logger.warning('Token file was not found. A new token will '
                                'be acquired and written to .helios_token.')
            self.get_token()

    def verify_token(self):
        """
        Verifies if the current token is still valid.

        If the token is bad or if the expiration time is less than the
        threshold False will be returned.

        Returns:
            bool: True if current token is valid, False otherwise.

        """
        resp = requests.get(self.api_url + '/session',
                            headers={self.token['name']: self.token['value']},
                            verify=True)
        resp.raise_for_status()

        json_resp = resp.json()

        # Get expiration time.
        expiration = json_resp['expires_in'] / 60.0

        if json_resp['name'] is None:
            return False
        elif expiration < self.token_expiration_threshold:
            self.logger.warning('Token is valid, but expires in %s minutes.',
                                expiration)
            return False
        else:
            self.logger.info('Token is valid for %d minutes.', expiration)
            return True
