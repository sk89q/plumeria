import base64
import functools
import random
import string
import urllib.parse
from datetime import datetime
from datetime import timedelta
from typing import Dict
from typing import List, Mapping, Optional
from typing import Tuple

from cachetools import TTLCache
from requests.structures import CaseInsensitiveDict

from plumeria.command import CommandError
from plumeria.transport import User
from plumeria.util.http import DefaultClientSession

NO_STORE_ERROR = "The bot doesn't have a plugin enabled that allows storing service authorizations."


def catch_token_expiration(endpoint):
    def decorator(f):
        @functools.wraps(f)
        async def wrapper(*args, **kwargs):
            try:
                return await f(*args, **kwargs)
            except TokenExpirationError:
                raise CommandError(
                    "Please connect your account to use this command. If you did it previously, then it means "
                    "that access expired or you revoked access. Use the `/connect {}` command.".format(endpoint.name))

        return wrapper

    return decorator


class TokenExpirationError(Exception):
    """Raised when the authorization codes for the user have expired."""


class FlowError(Exception):
    """Raised when something has happened with an authorization flow."""


class UnknownFlowError(FlowError):
    """
    Raised when there is no associated flow with the request.

    This might happen if the user goes to the redirect URL after it has already expired.

    """


class Endpoint:
    """
    Represents an OAuth endpoint.

    Attributes
    ----------
    name: str
        The name of the endpoint
    client_id: str
        The client ID
    client_secret: str
        The client secret
    auth_url: str
        The authorization URL that the user will be sent to
    token_url: str
        The URL used for server-to-server requests to fetch authorization and refresh tokens
    requested_scopes: List[str]
        A list of scopes to request
    auth_params: Optional[Mapping[str, str]]
        A mapping of extra query parameters to provide to the endpoint
    refresh_token_url: Optional[str]
        A URL to use for the refresh token if it is different from the one to get the initial access token
    grants: Dict[Tuple[str, str], :class:`Authorization`]
        A mapping of authorizations

    """

    def __init__(self, manager, name, client_id, client_secret, auth_url, token_url,
                 requested_scopes: List[str], auth_params: Mapping[str, str] = None, refresh_token_url: str = None):
        """Create a new instance."""

        self._manager = manager  # type: AccessManager
        self.name = name
        self._client_id = client_id
        self._client_secret = client_secret
        self.auth_url = auth_url
        self.auth_token_url = token_url
        self.refresh_token_url = refresh_token_url or token_url
        self.requested_scopes = requested_scopes
        self.auth_params = auth_params or []
        self.grants = {}  # type: Dict[Tuple[str, str], Authorization]

    @property
    def client_id(self):
        return self._client_id if isinstance(self._client_id, str) else self._client_id()

    @property
    def client_secret(self):
        return self._client_secret if isinstance(self._client_secret, str) else self._client_secret()

    async def request_authorization(self, user: User) -> str:
        """
        Begin the first step of an OAuth request which is to generate a URL that the
        user will visit to authorize the application.

        Parameters
        ----------
        user: :class:`User`
            The user that this flow is for

        Returns
        -------
        str
            A URL that the user can visit to start authorization
        """
        if not self._manager.store:
            raise NotImplementedError(NO_STORE_ERROR)

        params = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'redirect_uri': self._manager.redirect_uri,
            'state': self._manager._create_state(self, user),
            'scope': ' '.join(self.requested_scopes),
            'response_type': 'code',
        }
        params.update(self.auth_params)
        return self.auth_url + "?" + urllib.parse.urlencode(params)

    async def grant_authorization(self, transport: str, user: str, code: str):
        """
        Execute the second step of the OAuth flow, which is to exchange a secret code supplied
        by the service to get access and refresh tokens.
        """
        if not self._manager.store:
            raise NotImplementedError(NO_STORE_ERROR)

        params = {
            # 'client_id': self.client_id,
            # 'client_secret': self.client_secret,
            'grant_type': 'authorization_code',
            'redirect_uri': self._manager.redirect_uri,
            'code': code,
        }

        auth_header = 'Basic ' + base64.b64encode(
            "{}:{}".format(self.client_id, self.client_secret).encode('utf-8')).decode('ascii')

        async with DefaultClientSession() as session:
            async with session.post(self.auth_token_url,
                                    data=params,
                                    headers=(('Content-Type', 'application/x-www-form-urlencoded'),
                                             ('Authorization', auth_header))) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    auth = Authorization(
                        self.name,
                        transport,
                        user,
                        data['access_token'],
                        data['token_type'] if 'token_type' in data else 'Bearer',
                        datetime.utcnow() + timedelta(seconds=int(data['expires_in'])),
                        data['refresh_token']
                    )
                    await self._manager.store.put(auth)
                    self.grants[(transport, user)] = auth
                    return True
                else:
                    raise FlowError('did not receive 200 OK: ' + (await resp.text()))  # TODO: remove

    async def grant_access(self, transport: str, user: str, refresh_token: str):
        """
        Exchange the refresh token for an access token, which is needed when
        the access token expires.
        """
        if not self._manager.store:
            raise NotImplementedError(NO_STORE_ERROR)

        key = (transport, user)

        params = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
        }

        async with DefaultClientSession() as session:
            async with session.post(self.refresh_token_url,
                                    data=params,
                                    headers=(('Content-Type', 'application/x-www-form-urlencoded'),)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    new_auth = Authorization(
                        self.name,
                        transport,
                        user,
                        data['access_token'],
                        data['token_type'] if 'token_type' in data else 'Bearer',
                        datetime.utcnow() + timedelta(seconds=int(data['expires_in'])),
                        refresh_token  # previous refresh token
                    )
                    await self._manager.store.put(new_auth)
                    self.grants[key] = new_auth
                    return new_auth
                else:
                    raise FlowError('did not receive 200 OK')

    async def get_authorization(self, user: User):
        """
        Get an authorization to use in requests. If one is not readily available, then
        some HTTP requests may need to be executed.

        Parameters
        ----------
        user: :class:`User`
            The user to get the token for

        Returns
        -------
        Authorization:
            An authorization

        Raises
        ------
        TokenExpirationError:
            Raised if no access token can be provided because the user has to redo authorization

        """
        if not self._manager.store:
            raise NotImplementedError(NO_STORE_ERROR)

        key = (user.transport.id, user.id)
        try:
            auth = self.grants[key]
        except KeyError:
            auth = await self._manager.store.get(self.name, user.transport.id, user.id)
            self.grants[key] = auth  # cache so we don't hit the database again

        if auth is None:
            raise TokenExpirationError()
        elif auth.active:
            return auth
        else:  # need to request a new access token
            return await self.grant_access(user.transport.id, user.id, auth.refresh_token)

    async def get_auth_header(self, user: User):
        """
        Get the content of the Authorization: header to be sent with requests.

        Parameters
        ----------
        user: :class:`User`
            The user to get the header for

        Returns
        -------
        str:
            The header content

        """
        auth = await self.get_authorization(user)
        return "{} {}".format(auth.token_type, auth.access_token)

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name


class Authorization:
    """Holds the tokens that came from a flow. This data is to be persisted so it can be reused again."""

    __slots__ = ('endpoint_name', 'transport', 'user', 'access_token', 'token_type', 'expiration_at', 'refresh_token')

    def __init__(self, endpoint_name, transport, user, access_token, token_type, expiration_at, refresh_token):
        self.endpoint_name = endpoint_name
        self.transport = transport
        self.user = user
        self.access_token = access_token
        self.token_type = token_type
        self.expiration_at = expiration_at
        self.refresh_token = refresh_token

    @property
    def active(self):
        """Checks if the access token is still valid."""
        return self.expiration_at >= datetime.utcnow()


class TokenStore:
    """
    A token stores provides a way to save authorization tokens.
    """

    async def get(self, endpoint_name: str, transport: str, user: str):
        """
        Load an authorization token.

        Parameters
        ----------
        endpoint_name: str
            The name of the endpoint
        transport: str
            The ID of the transport
        user:
            The ID of the user

        Returns
        -------
        Optional[:class:`Authorization`]
            The authorization or None
        """
        raise NotImplementedError()

    async def put(self, auth: Authorization):
        """
        Save an authorization.

        Parameters
        ----------
        auth: Authorization
            The authorization

        """
        raise NotImplementedError()

    def remove(self, endpoint_name: str, transport: str, user: str):
        """
        Delete the authorization for a user.

        Parameters
        ----------
        endpoint_name: str
            The name of the endpoint
        transport: str
            The ID of the transport
        user:
            The ID of the user

        """
        raise NotImplementedError()


class AccessManager:
    """
    Manage authorizations to different services through OAuth.

    Users can start an authorization flow which will give the application access to certain
    actions.

    Attributes
    ----------
    redirect_uri: str
        The callback URL

    """

    STATE_TOKEN_LENGTH = 32

    def __init__(self, flow_expiration=60 * 15, flow_cache_size=1000):
        """
        Create a new access manager for managing authorizations.

        Parameters
        ----------
        flow_expiration: int
            The number of seconds to keep pending authorization flows in memory
        flow_cache_size: int
            The maximum number of pending authorization flows to keep in memory at a time

        """
        self.store = None
        self.endpoints = CaseInsensitiveDict()
        self.state_cache = TTLCache(maxsize=flow_cache_size,
                                    ttl=flow_expiration)  # type: Dict[Tuple[str, str], Tuple[Endpoint, str, str]]
        self.random = random.SystemRandom()
        self.redirect_uri = "http://localhost/oauth2/callback/"

    def add(self, endpoint):
        self.endpoints[endpoint.name] = endpoint
        return endpoint

    def create_oauth2(self, name, client_id, client_secret, auth_url, token_url, requested_scopes: List[str],
                      auth_params: Optional[Mapping[str, str]] = None,
                      refresh_token_url: Optional[str] = None) -> Endpoint:
        """
        Register a new endpoint for authorization.

        Parameters
        ----------
        name: str
            The name of the endpoint, like 'youtube' or 'spotify'
        client_id: str
            The client ID
        client_secret: str
            The client secret
        auth_url: str
            The URL that the user will visit to start authorization
        token_url: str
            The URL for server-to-server usage to obtain an access token
        requested_scopes: Sequence[str]
            A list of scopes (permissions) to request
        auth_params: Optional[Mapping[str, str]]
            A mapping of extra parameters to provide to auth_url (visible to the user in the URL. Some services
            let you provide extra options in the prompt
        refresh_token_url: Optional[str]
            A different URL for refreshing tokens, if needed, otherwise `token_url` will be used

        Returns
        -------
        :class:`Endpoint`
            An endpoint instance

        """
        endpoint = Endpoint(self, name, client_id, client_secret, auth_url, token_url, requested_scopes, auth_params,
                            refresh_token_url)
        return endpoint

    def _create_state(self, endpoint: Endpoint, user: User) -> str:
        """
        Creates a new state token and then registers this token as a pending flow.

        Parameters
        ----------
        endpoint: :class:`Endpoint`
            The endpoint
        user: :class:`User`
            The user that the authorization is for

        Returns
        -------
        str:
            The state token

        """
        # TODO: prevent denial of service via state cache exhaustion
        token = ''.join(
            self.random.choice(string.ascii_uppercase + string.digits) for _ in range(self.STATE_TOKEN_LENGTH))
        self.state_cache[token] = (endpoint, user.transport.id, user.id)
        return token

    async def process_request_authorization(self, state, code):
        """
        Process a callback from a request authorization that was successful.

        Parameters
        ----------
        state: str
            The state received from the service
        code: str
            The code received from the service

        """
        try:
            endpoint, transport, user = self.state_cache[state]
            del self.state_cache[state]
        except KeyError:
            raise UnknownFlowError()

        await endpoint.grant_authorization(transport, user, code)

    async def cancel_request_authorization(self, state, error) -> bool:
        """
        Process a callback from a request authorization that failed.

        Parameters
        ----------
        state: str
            The state received from the service
        code: str
            The code received from the service

        Returns
        -------
        bool:
            Whether the flow was pending or not

        """
        try:
            del self.state_cache[state]
            return True
        except KeyError:
            return False

    def get_endpoint(self, name):
        """
        Get an endpoint by name.

        Parameters
        ----------
        name: str
            The endpoint name

        Returns
        -------
        :class:`Endpoint`

        Raises
        ------
        KeyError:
            Thrown if the endpoint doesn't exist

        """
        return self.endpoints[name]


oauth_manager = AccessManager()
