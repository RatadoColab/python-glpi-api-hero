"""Security regressions of the transport: redirects, URLs, secrets in errors and logs."""

from __future__ import annotations

import logging

import pytest

from glpi_api_hero import Glpi
from glpi_api_hero.core.legacy_rest import LegacyRestConnector
from glpi_api_hero.exceptions import ConfigurationError, GlpiError
from tests.conftest import APP_TOKEN, BASE_URL, USER_TOKEN, GlpiMock

SESSION_SECRET = "test-session-token"


def test_redirects_are_not_followed(session: GlpiMock) -> None:
    """A 3xx never makes the client resend Session-Token/App-Token to another host."""
    session.override("GET", "Computer/1", 302, "", headers={"Location": "https://evil.example/steal"})
    with pytest.raises(GlpiError):
        Glpi.connector().get_item("Computer", 1)
    hosts = {call.request.url.split("/")[2] for call in session.rsps.calls}
    assert "evil.example" not in hosts


def test_url_with_credentials_is_rejected() -> None:
    """Credentials embedded in the URL would end up in logs and messages."""
    with pytest.raises(ConfigurationError):
        LegacyRestConnector("https://user:pw@glpi.example/apirest.php", APP_TOKEN, user_token=USER_TOKEN)


def test_plain_http_is_reported(caplog: pytest.LogCaptureFixture) -> None:
    """A plain http URL logs a warning (and never the tokens)."""
    with caplog.at_level(logging.WARNING, logger="glpi_api_hero"):
        LegacyRestConnector("http://glpi.example/apirest.php", APP_TOKEN, user_token=USER_TOKEN)
    assert "plain http" in caplog.text
    assert USER_TOKEN not in caplog.text


def test_secrets_are_not_in_connection_errors(session: GlpiMock) -> None:
    """Tokens never appear in the message of a connection error."""
    session.override("GET", "Computer/1", 200, None, error="connection")
    with pytest.raises(GlpiError) as info:
        Glpi.connector().get_item("Computer", 1)
    text = str(info.value) + repr(info.value) + repr(info.value.__cause__)
    for secret in (USER_TOKEN, APP_TOKEN, SESSION_SECRET):
        assert secret not in text


def test_secrets_are_not_in_logs_or_api_errors(session: GlpiMock, caplog: pytest.LogCaptureFixture) -> None:
    """Debug logs and API error messages do not carry tokens."""
    session.override("GET", "Computer/2", 400, ["ERROR_X", f"bad token {USER_TOKEN} {SESSION_SECRET}"])
    with caplog.at_level(logging.DEBUG, logger="glpi_api_hero"):
        with pytest.raises(GlpiError) as info:
            Glpi.connector().get_item("Computer", 2)
    for secret in (USER_TOKEN, SESSION_SECRET):
        assert secret not in str(info.value)
        assert secret not in caplog.text


def test_secrets_are_not_in_the_connector_repr() -> None:
    """The default repr of the connector does not expose tokens."""
    connector = LegacyRestConnector(BASE_URL, APP_TOKEN, user_token=USER_TOKEN)
    assert USER_TOKEN not in repr(connector)
    assert APP_TOKEN not in repr(connector)


@pytest.mark.parametrize("itemtype", ["../Config", "Computer/1", "Computer?x=1", "..", "Computer#"])
def test_itemtype_cannot_change_the_url_path(session: GlpiMock, itemtype: str) -> None:
    """Itemtypes are encoded or refused; the request path never gains extra segments."""
    try:
        Glpi.connector().get_item(itemtype, 1)
    except (GlpiError, ValueError):
        pass
    for call in session.captured():
        assert call["path"].count("/") <= 1
        assert "?" not in call["path"]
