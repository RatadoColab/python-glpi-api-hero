"""Exception hierarchy and the mapping of GLPI errors to exceptions."""

from __future__ import annotations

import pytest
import requests

from glpi_api_hero import Glpi
from glpi_api_hero.core.types import OperationResult
from glpi_api_hero.exceptions import (
    ERROR_CODE_CLASSES,
    AuthenticationError,
    BadRequestError,
    ConfigurationError,
    GlpiAPIError,
    GlpiConnectionError,
    GlpiError,
    NotFoundError,
    PartialOperationError,
    PermissionDeniedError,
    RateLimitError,
    ServerError,
    UnsupportedOperationError,
    error_class_for,
)
from tests.conftest import APP_TOKEN, BASE_URL, PASSWORD, USER_TOKEN, USERNAME, GlpiMock


def test_every_exception_derives_from_glpi_error() -> None:
    """A single ``except GlpiError`` catches everything the library raises."""
    for cls in (ConfigurationError, GlpiConnectionError, GlpiAPIError, BadRequestError, AuthenticationError,
                PermissionDeniedError, NotFoundError, RateLimitError, ServerError, PartialOperationError,
                UnsupportedOperationError):
        assert issubclass(cls, GlpiError)


@pytest.mark.parametrize(("status", "expected"), [
    (400, BadRequestError), (401, AuthenticationError), (403, PermissionDeniedError), (404, NotFoundError),
    (429, RateLimitError), (500, ServerError), (503, ServerError), (418, GlpiAPIError),
])
def test_status_without_error_key(status: int, expected: type[GlpiAPIError], session: GlpiMock) -> None:
    """Without a GLPI error key the HTTP status chooses the class.

    Args:
        status: HTTP status answered.
        expected: Expected exception class.
        session: Simulator with an open session.
    """
    session.override("GET", "Location/1", status, "plain text error")
    with pytest.raises(expected) as info:
        Glpi.connector().get_item("Location", 1)
    assert type(info.value) is expected
    assert info.value.status_code == status
    assert info.value.error_code is None


@pytest.mark.parametrize(("error_code", "expected"), sorted(ERROR_CODE_CLASSES.items()))
def test_every_glpi_error_key(error_code: str, expected: type[GlpiAPIError], session: GlpiMock) -> None:
    """Every known ``ERROR_*`` key maps to its class, whatever the status.

    Args:
        error_code: GLPI error key.
        expected: Expected exception class.
        session: Simulator with an open session.
    """
    session.override("GET", "Location/1", 400, [error_code, "detail"])
    with pytest.raises(expected) as info:
        Glpi.connector().get_item("Location", 1)
    assert info.value.error_code == error_code
    assert info.value.message == "detail"
    assert str(info.value) == f"({error_code}) detail"


def test_unknown_error_key_falls_back_to_status() -> None:
    """An unknown key uses the HTTP status; 429 always means rate limit."""
    assert error_class_for(404, "ERROR_FROM_A_PLUGIN") is NotFoundError
    assert error_class_for(429, "ERROR_BAD_ARRAY") is RateLimitError
    assert error_class_for(502, None) is ServerError


@pytest.mark.parametrize(("header", "expected"), [("12", 12.0), ("0.5", 0.5),
                                                  ("Wed, 21 Oct 2026 07:28:00 GMT", None), (None, None)])
def test_retry_after(header: str | None, expected: float | None, session: GlpiMock) -> None:
    """``Retry-After`` in seconds is exposed on ``RateLimitError``.

    Args:
        header: ``Retry-After`` value (``None`` for absent).
        expected: Expected ``retry_after``.
        session: Simulator with an open session.
    """
    headers = {"Retry-After": header} if header is not None else {}
    session.override("GET", "Location", 429, "Too Many Requests", headers=headers)
    with pytest.raises(RateLimitError) as info:
        Glpi.connector().get_all_items("Location")
    assert info.value.retry_after == expected


def test_network_error_is_chained(session: GlpiMock) -> None:
    """Network errors become ``GlpiConnectionError`` with the requests exception as cause.

    Args:
        session: Simulator with an open session.
    """
    session.override("GET", "Location/1", error="connection")
    with pytest.raises(GlpiConnectionError) as info:
        Glpi.connector().get_item("Location", 1)
    assert isinstance(info.value.__cause__, requests.exceptions.ConnectionError)


def test_messages_never_contain_secrets(glpi_mock: GlpiMock) -> None:
    """Tokens and passwords echoed by the server are redacted from messages.

    Args:
        glpi_mock: Active GLPI simulator.
    """
    glpi_mock.override("GET", "initSession", 401, ["ERROR_GLPI_LOGIN", f"refused {USER_TOKEN} for {APP_TOKEN}"])
    with pytest.raises(AuthenticationError) as info:
        Glpi.connect(BASE_URL, APP_TOKEN, user_token=USER_TOKEN)
    assert USER_TOKEN not in str(info.value)
    assert APP_TOKEN not in str(info.value)
    glpi_mock.override("GET", "initSession", 401, ["ERROR_GLPI_LOGIN", f"bad password {PASSWORD}"])
    with pytest.raises(AuthenticationError) as info:
        Glpi.connect(BASE_URL, APP_TOKEN, username=USERNAME, password=PASSWORD)
    assert PASSWORD not in str(info.value)
    assert "***" in str(info.value)


def test_partial_operation_error_lists_failures() -> None:
    """``PartialOperationError.failed`` keeps only the failed items."""
    results = [OperationResult(1, True), OperationResult(None, False, "Duplicate entry")]
    error = PartialOperationError("partial", results, error_code="ERROR_GLPI_PARTIAL_ADD")
    assert error.results == results
    assert error.failed == [results[1]]
    assert error.error_code == "ERROR_GLPI_PARTIAL_ADD"
