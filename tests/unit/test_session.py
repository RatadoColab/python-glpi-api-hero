"""Global session facade ``Glpi``."""

from __future__ import annotations

import logging
from pathlib import Path

import pytest

from glpi_api_hero import Glpi
from glpi_api_hero.exceptions import AuthenticationError, ConfigurationError, NotFoundError, ServerError
from tests.conftest import APP_TOKEN, BASE_URL, SESSION_TOKEN, USER_TOKEN, GlpiMock


def _paths(glpi_mock: GlpiMock) -> list[str]:
    """List the method and path of the captured requests.

    Args:
        glpi_mock: Active GLPI simulator.

    Returns:
        ``"METHOD path"`` strings.
    """
    return [f"{r['method']} {r['path']}" for r in glpi_mock.captured()]


def test_connect_and_disconnect(glpi_mock: GlpiMock) -> None:
    """``connect`` opens the session with the user token and ``disconnect`` kills it.

    Args:
        glpi_mock: Active GLPI simulator.
    """
    Glpi.connect(BASE_URL, APP_TOKEN, user_token=USER_TOKEN)
    assert Glpi.is_connected()
    init = glpi_mock.captured()[0]
    assert init["headers"] == {"App-Token": APP_TOKEN, "Authorization": f"user_token {USER_TOKEN}"}
    Glpi.connector().get_config()
    assert glpi_mock.captured()[1]["headers"] == {"App-Token": APP_TOKEN, "Session-Token": SESSION_TOKEN}
    Glpi.disconnect()
    assert not Glpi.is_connected()
    assert _paths(glpi_mock) == ["GET initSession", "GET getGlpiConfig", "GET killSession"]
    # Idempotent: a second call sends nothing
    Glpi.disconnect()
    assert len(glpi_mock.captured()) == 3


def test_connect_without_app_token(glpi_mock: GlpiMock) -> None:
    """The App-Token header is optional.

    Args:
        glpi_mock: Active GLPI simulator.
    """
    Glpi.connect(BASE_URL, user_token=USER_TOKEN)
    assert "App-Token" not in glpi_mock.captured()[0]["headers"]


def test_connect_twice_closes_previous_session(glpi_mock: GlpiMock) -> None:
    """A new ``connect`` logs in first and only then kills the previous session.

    Args:
        glpi_mock: Active GLPI simulator.
    """
    Glpi.connect(BASE_URL, APP_TOKEN, user_token=USER_TOKEN)
    Glpi.connect(BASE_URL, APP_TOKEN, user_token=USER_TOKEN)
    assert _paths(glpi_mock) == ["GET initSession", "GET initSession", "GET killSession"]


def test_failed_reconnect_keeps_the_current_session(glpi_mock: GlpiMock) -> None:
    """A refused new login leaves the working session untouched.

    Args:
        glpi_mock: Active GLPI simulator.
    """
    Glpi.connect(BASE_URL, APP_TOKEN, user_token=USER_TOKEN)
    connector = Glpi.connector()
    glpi_mock.override("GET", "initSession", 401, ["ERROR_GLPI_LOGIN", "refused"])
    with pytest.raises(AuthenticationError):
        Glpi.connect(BASE_URL, APP_TOKEN, user_token="other")
    assert Glpi.is_connected()
    assert Glpi.connector() is connector


def test_session_context_manager(glpi_mock: GlpiMock) -> None:
    """``Glpi.session`` disconnects at the end of the block.

    Args:
        glpi_mock: Active GLPI simulator.
    """
    with Glpi.session(BASE_URL, APP_TOKEN, user_token=USER_TOKEN) as glpi:
        assert glpi is Glpi
        assert Glpi.is_connected()
    assert not Glpi.is_connected()
    assert _paths(glpi_mock)[-1] == "GET killSession"


def test_session_context_manager_disconnects_on_error(glpi_mock: GlpiMock) -> None:
    """``Glpi.session`` disconnects even when the block raises.

    Args:
        glpi_mock: Active GLPI simulator.
    """
    with pytest.raises(RuntimeError), Glpi.session(BASE_URL, APP_TOKEN, user_token=USER_TOKEN):
        raise RuntimeError("boom")
    assert not Glpi.is_connected()
    assert _paths(glpi_mock) == ["GET initSession", "GET killSession"]


def test_verify_tls_default(glpi_mock: GlpiMock) -> None:
    """TLS certificates are verified unless explicitly disabled.

    Args:
        glpi_mock: Active GLPI simulator.
    """
    Glpi.connect(BASE_URL, APP_TOKEN, user_token=USER_TOKEN)
    assert Glpi.connector().verify is True


def test_verify_tls_ca_bundle_and_disabled(glpi_mock: GlpiMock, caplog: pytest.LogCaptureFixture,
                                           tmp_path: Path) -> None:
    """A CA bundle path is accepted; disabling TLS logs a warning.

    Args:
        glpi_mock: Active GLPI simulator.
        caplog: Log capture.
        tmp_path: Temporary directory.
    """
    bundle = tmp_path / "ca.pem"
    bundle.write_text("-----BEGIN CERTIFICATE-----")
    Glpi.connect(BASE_URL, APP_TOKEN, user_token=USER_TOKEN, verify_tls=str(bundle))
    assert Glpi.connector().verify == str(bundle)
    with caplog.at_level(logging.WARNING, logger="glpi_api_hero"):
        Glpi.connect(BASE_URL, APP_TOKEN, user_token=USER_TOKEN, verify_tls=False)
    assert Glpi.connector().verify is False
    assert any("TLS certificate verification is disabled" in rec.message for rec in caplog.records)


def test_profile_and_entity_only_sent_when_changed(session: GlpiMock) -> None:
    """``set_profile_entity`` skips the API when nothing changes; a profile change resends the entity.

    Args:
        session: Simulator with an open session.
    """
    Glpi.set_profile_entity(4, 1)
    Glpi.set_profile_entity(4, 1)
    Glpi.set_profile_entity(4, 1, is_recursive=False)
    Glpi.set_profile_entity(5, 1, is_recursive=False)
    assert _paths(session) == ["POST changeActiveProfile", "POST changeActiveEntities",
                               "POST changeActiveEntities", "POST changeActiveProfile", "POST changeActiveEntities"]
    assert session.captured()[1]["body"] == {"entities_id": 1, "is_recursive": True}
    assert session.captured()[2]["body"] == {"entities_id": 1, "is_recursive": False}


def test_profile_and_entity_reset_after_disconnect(session: GlpiMock) -> None:
    """After a new login the profile and entity are sent again.

    Args:
        session: Simulator with an open session.
    """
    Glpi.set_profile_entity(4, 1)
    Glpi.connect(BASE_URL, APP_TOKEN, user_token=USER_TOKEN)
    session.reset_calls()
    Glpi.set_profile_entity(4, 1)
    assert _paths(session) == ["POST changeActiveProfile", "POST changeActiveEntities"]


def test_configuration_errors(glpi_mock: GlpiMock) -> None:
    """Missing session, URL or credentials raise ``ConfigurationError`` without any request.

    Args:
        glpi_mock: Active GLPI simulator.
    """
    with pytest.raises(ConfigurationError):
        Glpi.connector()
    with pytest.raises(ConfigurationError):
        Glpi.connect(BASE_URL, APP_TOKEN)
    with pytest.raises(ConfigurationError):
        Glpi.connect("", APP_TOKEN, user_token=USER_TOKEN)
    with pytest.raises(ConfigurationError):
        Glpi.connect(BASE_URL, APP_TOKEN, username="someone")
    with pytest.raises(ConfigurationError):
        Glpi.set_profile_entity(4, 0)
    assert glpi_mock.captured() == []


def test_logged_user_is_cached(session: GlpiMock) -> None:
    """``logged_user`` reads the session user once.

    Args:
        session: Simulator with an open session.
    """
    first = Glpi.logged_user()
    second = Glpi.logged_user()
    assert first == second
    assert first["id"] == 2
    assert _paths(session) == ["GET getFullSession", "GET User/2"]


def test_get_config_and_multiple(session: GlpiMock) -> None:
    """``get_config`` and ``get_multiple`` call the matching endpoints.

    Args:
        session: Simulator with an open session.
    """
    assert Glpi.get_config()["cfg_glpi"]["version"] == "10.0.26"
    assert Glpi.get_multiple([]) == []
    Glpi.get_multiple([("User", 2), ("Computer", 3)], expand_dropdowns=True)
    request = session.captured()[-1]
    assert request["path"] == "getMultipleItems"
    assert request["query"] == {"expand_dropdowns": "true", "items[0][itemtype]": "User", "items[0][items_id]": "2",
                                "items[1][itemtype]": "Computer", "items[1][items_id]": "3"}


def test_set_profile_not_found(session: GlpiMock) -> None:
    """An unknown profile raises ``NotFoundError``.

    Args:
        session: Simulator with an open session.
    """
    session.override("POST", "changeActiveProfile", 404, ["ERROR_ITEM_NOT_FOUND", "Item not found"])
    with pytest.raises(NotFoundError):
        Glpi.set_profile_entity(99, None)


def test_glpi_is_not_instantiable() -> None:
    """``Glpi`` is a class-level facade."""
    with pytest.raises(TypeError):
        Glpi()


@pytest.mark.parametrize("value", ["", 0, None, "/no/such/ca.pem"])
def test_invalid_verify_tls_values(value: object, glpi_mock: GlpiMock) -> None:
    """Falsy non-boolean values or missing CA paths never disable TLS silently.

    Args:
        value: Invalid ``verify_tls``.
        glpi_mock: Active GLPI simulator.
    """
    with pytest.raises(ConfigurationError):
        Glpi.connect(BASE_URL, APP_TOKEN, user_token=USER_TOKEN, verify_tls=value)  # type: ignore[arg-type]
    assert glpi_mock.captured() == []


def test_reconnect_after_expired_session(session: GlpiMock, caplog: pytest.LogCaptureFixture) -> None:
    """A failed logout of the old session does not prevent a new login.

    Args:
        session: Simulator with an open session.
        caplog: Log capture.
    """
    session.override("GET", "killSession", 401, ["ERROR_SESSION_TOKEN_INVALID", "expired"])
    with caplog.at_level(logging.WARNING, logger="glpi_api_hero"):
        Glpi.connect(BASE_URL, APP_TOKEN, user_token=USER_TOKEN)
    assert Glpi.is_connected()
    assert any("could not close the previous GLPI session" in rec.message for rec in caplog.records)


def test_block_error_wins_over_logout_error(glpi_mock: GlpiMock) -> None:
    """The error raised in a ``with`` block is not replaced by a logout failure.

    Args:
        glpi_mock: Active GLPI simulator.
    """
    glpi_mock.override("GET", "killSession", 500, ["ERROR_UNKNOWN", "boom"])
    with pytest.raises(KeyError), Glpi.session(BASE_URL, APP_TOKEN, user_token=USER_TOKEN):
        raise KeyError("original")
    assert not Glpi.is_connected()
    with pytest.raises(ServerError), Glpi.session(BASE_URL, APP_TOKEN, user_token=USER_TOKEN):
        pass


def test_failed_login_releases_the_connector(glpi_mock: GlpiMock, monkeypatch: pytest.MonkeyPatch) -> None:
    """The HTTP pool of a connector whose login failed is closed.

    Args:
        glpi_mock: Active GLPI simulator.
        monkeypatch: Pytest monkeypatch.
    """
    import requests

    closed = []
    original = requests.Session.close
    monkeypatch.setattr(requests.Session, "close", lambda self: (closed.append(self), original(self)))
    glpi_mock.override("GET", "initSession", 401, ["ERROR_GLPI_LOGIN", "refused"])
    with pytest.raises(AuthenticationError):
        Glpi.connect(BASE_URL, APP_TOKEN, user_token=USER_TOKEN)
    assert len(closed) == 1
    assert not Glpi.is_connected()
