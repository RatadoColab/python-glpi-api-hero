"""Former session API (``ApiCommunication``), kept only for the characterization tests.

The library no longer ships it (removed in phase 04.1, D32). The scenarios that recorded the
session behavior of point A still run through this copy, so the HTTP requests and results of
``Glpi`` stay pinned by the same oracle.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from glpi_api_hero.core.connector import Connector
from glpi_api_hero.core.session import Glpi


class ApiCommunication:
    """Former static session API delegating to :class:`Glpi`."""

    # Parameters given to setConnectionParameters, used by initSession
    glpi_connection: dict[str, Any] = {"url": "", "apptoken": "", "usertoken": "", "user": None, "passwd": None}
    # Profile and entity requested by setProfileEntity
    glpi_environment: dict[str, Any] = {"profiles_id": None, "entities_id": None, "is_recursive": True}

    @staticmethod
    def setConnectionParameters(url: str, apptoken: str, usertoken: str | None = None, user: str | None = None,
                                passwd: str | None = None) -> None:
        """Store the connection parameters (no request is sent).

        Args:
            url: Base URL of ``apirest.php``.
            apptoken: Application token.
            usertoken: User API token.
            user: Login; when given, it is used instead of the user token.
            passwd: Password of ``user``.
        """
        ApiCommunication.glpi_connection = {"url": url, "apptoken": apptoken, "usertoken": usertoken,
                                            "user": user, "passwd": passwd}

    @staticmethod
    def initSession(verify_certs: bool | str = True) -> bool:
        """Open the session with the stored parameters, unless one is already open.

        Args:
            verify_certs: TLS verification (``True`` by default, or a CA bundle path).

        Returns:
            ``True`` once the session is open.

        Raises:
            ConfigurationError: When the parameters are missing.
            AuthenticationError: When the credentials are refused.
            GlpiConnectionError: When the server cannot be reached.
        """
        if not Glpi.is_connected():
            conn = ApiCommunication.glpi_connection
            if conn["user"] is None:
                Glpi.connect(conn["url"], conn["apptoken"], user_token=conn["usertoken"], verify_tls=verify_certs)
            else:
                Glpi.connect(conn["url"], conn["apptoken"], username=conn["user"], password=conn["passwd"],
                             verify_tls=verify_certs)
        return True

    @staticmethod
    def killSession() -> None:
        """Close the session; does nothing when no session is open."""
        ApiCommunication.glpi_environment = {"profiles_id": None, "entities_id": None, "is_recursive": True}
        Glpi.disconnect()

    @staticmethod
    def setProfileEntity(profiles_id: int, entities_id: int, is_recursive: bool = True) -> bool:
        """Activate a profile and an entity (opening the session when needed).

        Args:
            profiles_id: Profile id.
            entities_id: Entity id.
            is_recursive: Also activate the sub-entities.

        Returns:
            ``True`` once applied.
        """
        ApiCommunication.glpi_environment = {"profiles_id": profiles_id, "entities_id": entities_id,
                                             "is_recursive": is_recursive}
        ApiCommunication.initSession()
        Glpi.set_profile_entity(profiles_id, entities_id, is_recursive)
        return True

    @staticmethod
    def getLoggedUser() -> dict[str, Any]:
        """Return the logged user (opening the session when needed).

        Returns:
            The ``User`` item of the session.
        """
        ApiCommunication.initSession()
        return Glpi.logged_user()

    @staticmethod
    def getConn() -> Connector | None:
        """Return the active connector.

        Returns:
            The connector, or ``None`` when no session is open.
        """
        return Glpi.connector() if Glpi.is_connected() else None

    @staticmethod
    def call(fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """Call a connector method (errors are already library exceptions).

        Args:
            fn: Callable to run.
            *args: Positional arguments.
            **kwargs: Keyword arguments.

        Returns:
            The result of ``fn``.
        """
        return fn(*args, **kwargs)
