"""Security regressions of the transport: redirects, URLs, secrets in errors and logs."""

from __future__ import annotations

import logging

import pytest

from glpi_api_hero import Glpi
from glpi_api_hero.core.legacy_rest import LegacyRestConnector
from glpi_api_hero.exceptions import BadRequestError, ConfigurationError, GlpiError
from tests.conftest import APP_TOKEN, BASE_URL, SESSION_TOKEN, USER_TOKEN, GlpiMock


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
    with caplog.at_level(logging.WARNING, logger="glpi_api_hero"), pytest.warns(UserWarning):
        LegacyRestConnector("http://glpi.example/apirest.php", APP_TOKEN, user_token=USER_TOKEN)
    assert "plain http" in caplog.text
    assert USER_TOKEN not in caplog.text


def test_secrets_are_not_in_connection_errors(session: GlpiMock) -> None:
    """Tokens never appear in the message of a connection error."""
    session.override("GET", "Computer/1", 200, None, error="connection")
    with pytest.raises(GlpiError) as info:
        Glpi.connector().get_item("Computer", 1)
    text = str(info.value) + repr(info.value) + repr(info.value.__cause__)
    for secret in (USER_TOKEN, APP_TOKEN, SESSION_TOKEN):
        assert secret not in text


def test_secrets_are_not_in_logs_or_api_errors(session: GlpiMock, caplog: pytest.LogCaptureFixture) -> None:
    """Debug logs and API error messages do not carry tokens."""
    session.override("GET", "Computer/2", 400, ["ERROR_X", f"bad token {USER_TOKEN} {SESSION_TOKEN}"])
    with caplog.at_level(logging.DEBUG, logger="glpi_api_hero"):
        with pytest.raises(GlpiError) as info:
            Glpi.connector().get_item("Computer", 2)
    for secret in (USER_TOKEN, SESSION_TOKEN):
        assert secret not in str(info.value)
        assert secret not in caplog.text


def test_secrets_are_not_in_the_connector_repr() -> None:
    """The default repr of the connector does not expose tokens."""
    connector = LegacyRestConnector(BASE_URL, APP_TOKEN, user_token=USER_TOKEN)
    assert USER_TOKEN not in repr(connector)
    assert APP_TOKEN not in repr(connector)


@pytest.mark.parametrize(("itemtype", "path"), [
    ("Computer", "Computer/1"), ("Computer/1", "Computer%2F1/1"), ("Computer?x=1", "Computer%3Fx%3D1/1"),
    ("Computer#", "Computer%23/1"),
])
def test_itemtype_is_percent_encoded_in_the_path(session: GlpiMock, itemtype: str, path: str) -> None:
    """Itemtypes cannot add path segments, a query or a fragment."""
    Glpi.connector().get_item(itemtype, 1)
    assert session.captured()[0]["path"] == path
    assert session.captured()[0]["query"] == {}


def test_dot_segments_are_refused(session: GlpiMock) -> None:
    """``..`` is rejected before any request."""
    with pytest.raises(BadRequestError):
        Glpi.connector().get_item("..", 1)
    assert session.captured() == []


@pytest.mark.parametrize("status", [301, 302, 307, 308])
def test_redirect_answers_are_a_configuration_error(session: GlpiMock, status: int) -> None:
    """Any 3xx explains that the final URL must be configured; GET, POST and downloads all stop."""
    session.override("GET", "Computer/1", status, "", headers={"Location": "https://evil.example/x"})
    session.override("POST", "Computer", status, "", headers={"Location": "https://evil.example/x"})
    with pytest.raises(ConfigurationError, match="redirect"):
        Glpi.connector().get_item("Computer", 1)
    with pytest.raises(ConfigurationError, match="redirect"):
        Glpi.connector().add_items("Computer", [{"name": "x"}])
    assert {call.request.url.split("/")[2] for call in session.rsps.calls} == {BASE_URL.split("/")[2]}


@pytest.mark.parametrize("url", ["https://[::1/apirest.php", "glpi.example/apirest.php", "ftp://glpi/x",
                                 "https://glpi.example/apirest.php?token=x", "https://glpi.example/a#frag"])
def test_invalid_urls_are_a_configuration_error(url: str) -> None:
    """Malformed URLs fail with the library error before any request."""
    with pytest.raises(ConfigurationError):
        LegacyRestConnector(url, APP_TOKEN, user_token=USER_TOKEN)


def test_https_does_not_warn(caplog: pytest.LogCaptureFixture) -> None:
    """Only plain http (any case) is reported."""
    with caplog.at_level(logging.WARNING, logger="glpi_api_hero"):
        LegacyRestConnector("https://glpi.example/apirest.php", APP_TOKEN, user_token=USER_TOKEN)
        assert caplog.text == ""
        with pytest.warns(UserWarning):
            LegacyRestConnector("HTTP://glpi.example/apirest.php", APP_TOKEN, user_token=USER_TOKEN)
    assert "plain http" in caplog.text


def test_userinfo_is_not_logged_when_tls_is_disabled(caplog: pytest.LogCaptureFixture) -> None:
    """The TLS warning names only the host, and the credentials in the URL are refused."""
    with caplog.at_level(logging.WARNING, logger="glpi_api_hero"), pytest.raises(ConfigurationError):
        Glpi.connect("https://admin:s3cret@glpi.example/apirest.php", "a", user_token="t", verify_tls=False)
    assert "s3cret" not in caplog.text
