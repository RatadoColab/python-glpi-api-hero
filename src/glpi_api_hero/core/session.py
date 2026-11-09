"""Global session facade: one GLPI session per process.

Example::

    from glpi_api_hero import Glpi

    with Glpi.session("https://glpi.example/apirest.php", "app-token", user_token="user-token"):
        Glpi.set_profile_entity(4, 0)
        config = Glpi.get_config()

The session is global and shared by every model; it is not safe to use different
profiles or entities from several threads at the same time.
"""

from __future__ import annotations

import contextlib
import logging
from collections.abc import Iterator, Sequence
from typing import Any

from glpi_api_hero.core.connector import Connector
from glpi_api_hero.core.legacy_rest import DEFAULT_TIMEOUT, LegacyRestConnector
from glpi_api_hero.exceptions import ConfigurationError

logger = logging.getLogger("glpi_api_hero")


class Glpi:
    """Class-level facade over the active :class:`Connector` (never instantiated)."""

    _connector: Connector | None = None
    # Last profile/entity sent to the server, to skip redundant calls
    _profile: int | None = None
    _entity: tuple[int, bool] | None = None
    _logged_user: dict[str, Any] | None = None

    def __init__(self) -> None:
        """Forbid instances: every member is a class method.

        Raises:
            TypeError: Always.
        """
        raise TypeError("Glpi is a class-level facade; call its class methods directly")

    @classmethod
    def connect(cls, url: str, app_token: str | None = None, *, user_token: str | None = None,
                username: str | None = None, password: str | None = None, verify_tls: bool | str = True,
                timeout: float = DEFAULT_TIMEOUT, connector_class: type[Connector] = LegacyRestConnector) -> None:
        """Open the global session (closing the previous one, if any).

        Args:
            url: Base URL of the API (e.g. ``https://glpi.example/apirest.php``).
            app_token: Application token, when the API client requires one.
            user_token: User API token (used when no username is given).
            username: Login for Basic authentication.
            password: Password for Basic authentication.
            verify_tls: ``True`` to verify TLS (default), ``False`` to skip it, or a CA bundle path.
            timeout: Timeout in seconds of every request.
            connector_class: Connector implementation.

        Raises:
            ConfigurationError: When the URL or the credentials are missing.
            AuthenticationError: When the credentials are refused.
            GlpiConnectionError: When the server cannot be reached.
        """
        if not url:
            raise ConfigurationError("the GLPI API URL is required")
        if not username and not user_token:
            raise ConfigurationError("a user token or a username and password are required")
        if verify_tls is False:
            logger.warning("TLS certificate verification is disabled for %s", url)
        # The connector validates its parameters before the current session is closed
        connector = connector_class(url, app_token, user_token=user_token, username=username, password=password,
                                    verify=verify_tls, timeout=timeout)
        cls.disconnect()
        connector.init_session()
        cls._connector = connector

    @classmethod
    def disconnect(cls) -> None:
        """Close the global session; does nothing when no session is open."""
        connector = cls._connector
        cls._connector = None
        cls._profile = None
        cls._entity = None
        cls._logged_user = None
        if connector is not None:
            connector.kill_session()

    @classmethod
    @contextlib.contextmanager
    def session(cls, url: str, app_token: str | None = None, **kwargs: Any) -> Iterator[type[Glpi]]:
        """Open the session for a ``with`` block and always close it.

        Args:
            url: Base URL of the API.
            app_token: Application token.
            **kwargs: Keyword arguments of :meth:`connect`.

        Yields:
            The ``Glpi`` class.
        """
        cls.connect(url, app_token, **kwargs)
        try:
            yield cls
        finally:
            cls.disconnect()

    @classmethod
    def is_connected(cls) -> bool:
        """Tell whether a session is open.

        Returns:
            ``True`` when a session is open.
        """
        return cls._connector is not None

    @classmethod
    def connector(cls) -> Connector:
        """Return the active connector.

        Returns:
            The connector of the open session.

        Raises:
            ConfigurationError: When no session is open.
        """
        if cls._connector is None:
            raise ConfigurationError("no GLPI session: call Glpi.connect() or use Glpi.session() first")
        return cls._connector

    @classmethod
    def set_profile_entity(cls, profiles_id: int | None, entities_id: int | None, is_recursive: bool = True) -> None:
        """Activate a profile and an entity, calling the API only when they change.

        Args:
            profiles_id: Profile id (``None`` keeps the current one).
            entities_id: Entity id (``None`` keeps the current one).
            is_recursive: Also activate the sub-entities.

        Raises:
            ConfigurationError: When no session is open.
        """
        connector = cls.connector()
        if profiles_id is not None and profiles_id != cls._profile:
            connector.set_active_profile(profiles_id)
            cls._profile = profiles_id
            cls._logged_user = None
        if entities_id is not None and (entities_id, is_recursive) != cls._entity:
            connector.set_active_entities(entities_id, is_recursive)
            cls._entity = (entities_id, is_recursive)

    @classmethod
    def logged_user(cls) -> dict[str, Any]:
        """Return the logged user (cached until the session or the profile changes).

        Returns:
            The ``User`` item of the session.
        """
        if cls._logged_user is None:
            connector = cls.connector()
            session = connector.get_full_session()
            cls._logged_user = connector.get_item("User", int(session["glpiID"]))
        return cls._logged_user

    @classmethod
    def get_config(cls) -> dict[str, Any]:
        """Return the GLPI configuration visible to the session.

        Returns:
            The configuration.
        """
        return cls.connector().get_config()

    @classmethod
    def get_multiple(cls, refs: Sequence[tuple[str, int]], **params: Any) -> list[dict[str, Any]]:
        """Return several items of possibly different itemtypes in one request.

        Args:
            refs: ``(itemtype, id)`` pairs.
            **params: Extra API parameters.

        Returns:
            The items, in the order of ``refs``.
        """
        if not refs:
            return []
        return cls.connector().get_multiple_items(refs, **params)

    @classmethod
    def _reset(cls) -> None:
        """Drop the session state without calling the server (used by tests)."""
        connector = cls._connector
        cls._connector = None
        cls._profile = None
        cls._entity = None
        cls._logged_user = None
        # Release pooled HTTP connections
        http = getattr(connector, "_http", None)
        if http is not None:
            http.close()
