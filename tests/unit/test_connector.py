"""Legacy REST connector: transport details reproduced from the former glpi-api client."""

from __future__ import annotations

import logging
from pathlib import Path

import pytest

from glpi_api_hero import Glpi
from glpi_api_hero.core.legacy_rest import LegacyRestConnector
from glpi_api_hero.core.types import OperationResult
from glpi_api_hero.exceptions import (
    BadRequestError,
    ConfigurationError,
    GlpiConnectionError,
    PartialOperationError,
)
from tests.conftest import BASE_URL, USER_TOKEN, GlpiMock


def _connector() -> LegacyRestConnector:
    """Return the connector of the open session.

    Returns:
        The legacy connector.
    """
    connector = Glpi.connector()
    assert isinstance(connector, LegacyRestConnector)
    return connector


def test_get_all_items_accepts_206(session: GlpiMock, caplog: pytest.LogCaptureFixture) -> None:
    """Partial content is a valid page and its Content-Range is logged.

    Args:
        session: Simulator with an open session.
        caplog: Log capture.
    """
    session.override("GET", "Location", 206, [{"id": 1}], headers={"Content-Range": "0-0/9"})
    with caplog.at_level(logging.DEBUG, logger="glpi_api_hero"):
        assert _connector().get_all_items("Location", range="0-0") == [{"id": 1}]
    assert any("0-0/9" in rec.getMessage() for rec in caplog.records)


def test_search_accepts_206_and_dict_rows(session: GlpiMock) -> None:
    """Search returns the ``data`` rows for 200/206, also when GLPI indexes them by id.

    Args:
        session: Simulator with an open session.
    """
    session.override("GET", "search/Computer", 206, {"totalcount": 9, "data": {"7": {"1": "a"}, "8": {"1": "b"}}})
    assert _connector().search("Computer", [{"field": 1, "searchtype": "contains", "value": "x"}]) == [
        {"1": "a"}, {"1": "b"}]


def test_add_207_raises_partial_with_results(session: GlpiMock) -> None:
    """HTTP 207 on a bulk write carries every per-item result.

    Args:
        session: Simulator with an open session.
    """
    session.override("POST", "Location", 207, ["ERROR_GLPI_PARTIAL_ADD",
                                               [{"id": 5, "message": ""}, {"id": False, "message": "Duplicate"}]])
    with pytest.raises(PartialOperationError) as info:
        _connector().add_items("Location", [{"name": "a"}, {"name": "a"}])
    assert info.value.results == [OperationResult(5, True, ""), OperationResult(None, False, "Duplicate")]
    assert info.value.error_code == "ERROR_GLPI_PARTIAL_ADD"


def test_bulk_failure_of_every_item_is_partial(session: GlpiMock) -> None:
    """400 with per-item results (every item failed) is reported as ``PartialOperationError``.

    Args:
        session: Simulator with an open session.
    """
    session.override("DELETE", "Location", 400, ["ERROR_GLPI_DELETE", [{"7": False, "message": "Item not found"},
                                                                        {"8": False, "message": "Item not found"}]])
    with pytest.raises(PartialOperationError) as info:
        _connector().delete_items("Location", [7, 8])
    assert [result.id for result in info.value.failed] == [7, 8]


def test_delete_flags_and_204(session: GlpiMock) -> None:
    """Only non-default delete flags are sent; 204 without body means success.

    Args:
        session: Simulator with an open session.
    """
    session.override("DELETE", "Location", 204, "")
    assert _connector().delete_items("Location", [7], force_purge=True, history=False) == [OperationResult(7, True)]
    request = session.captured()[0]
    assert request["query"] == {"force_purge": "true", "history": "false"}
    assert request["body"] == {"input": [{"id": 7}]}


def test_timeout_raises_connection_error(session: GlpiMock) -> None:
    """A timeout becomes ``GlpiConnectionError``.

    Args:
        session: Simulator with an open session.
    """
    session.override("GET", "Location/1", error="timeout")
    with pytest.raises(GlpiConnectionError, match="timeout"):
        _connector().get_item("Location", 1)


def test_timeout_is_sent_with_every_request(glpi_mock: GlpiMock, monkeypatch: pytest.MonkeyPatch) -> None:
    """The configured timeout reaches ``requests``.

    Args:
        glpi_mock: Active GLPI simulator.
        monkeypatch: Pytest monkeypatch.
    """
    Glpi.connect(BASE_URL, user_token=USER_TOKEN, timeout=4.5)
    seen = []
    original = _connector()._http.request

    def spy(*args: object, **kwargs: object) -> object:
        """Record the timeout before sending."""
        seen.append(kwargs.get("timeout"))
        return original(*args, **kwargs)

    monkeypatch.setattr(_connector()._http, "request", spy)
    _connector().get_config()
    assert seen == [4.5]


def test_uid_translation_is_cached(session: GlpiMock) -> None:
    """Field uids become ids through listSearchOptions, loaded once per itemtype.

    Args:
        session: Simulator with an open session.
    """
    connector = _connector()
    connector.search("Computer", [{"field": "serial", "searchtype": "equals", "value": "A"}],
                     forcedisplay=["Entity.completename", 1])
    connector.search("Computer", [{"field": "name", "searchtype": "equals", "value": "B"}])
    paths = [request["path"] for request in session.captured()]
    assert paths == ["listSearchOptions/Computer", "search/Computer", "search/Computer"]
    query = session.captured()[1]["query"]
    assert query["criteria[0][field]"] == "5"
    assert query["forcedisplay[0]"] == "80"
    assert query["forcedisplay[1]"] == "1"
    assert connector.field_uid("Computer", 80) == "Entity.completename"


def test_unknown_uid_raises_bad_request(session: GlpiMock) -> None:
    """An unknown uid fails before the search request.

    Args:
        session: Simulator with an open session.
    """
    with pytest.raises(BadRequestError):
        _connector().search("Computer", [{"field": "nope", "searchtype": "equals", "value": "x"}])
    with pytest.raises(BadRequestError):
        _connector().field_uid("Computer", 999)
    assert [request["path"] for request in session.captured()] == ["listSearchOptions/Computer"]


def test_quotes_escaped_and_inputs_not_mutated(session: GlpiMock) -> None:
    """Single quotes are doubled in values; criteria lists are not modified.

    Args:
        session: Simulator with an open session.
    """
    criteria = [{"field": 1, "searchtype": "equals", "value": "o'neil"}]
    meta = [{"link": "AND", "itemtype": "Monitor", "field": 1, "searchtype": "contains", "value": "m"}]
    snapshot = (repr(criteria), repr(meta))
    _connector().search("User", criteria, metacriteria=meta)
    query = session.captured()[0]["query"]
    assert query["criteria[0][value]"] == "o''neil"
    assert query["criteria[1][meta]"] == "True"
    assert (repr(criteria), repr(meta)) == snapshot


def test_criteria_must_be_a_list(session: GlpiMock) -> None:
    """A dict instead of a list of criteria is a programming error.

    Args:
        session: Simulator with an open session.
    """
    with pytest.raises(TypeError):
        _connector().search("User", {"field": 1})  # type: ignore[arg-type]


def test_booleans_and_search_text(session: GlpiMock) -> None:
    """Booleans are sent as ``true``/``false`` and searchText is expanded.

    Args:
        session: Simulator with an open session.
    """
    _connector().get_all_items("Location", is_deleted=True, searchText={"name": "HQ"})
    assert session.captured()[0]["query"] == {"is_deleted": "true", "searchText[name]": "HQ"}


def test_upload_document(session: GlpiMock, tmp_path: Path) -> None:
    """Upload sends a multipart manifest and returns the created id.

    Args:
        session: Simulator with an open session.
        tmp_path: Temporary directory.
    """
    source = tmp_path / "report.txt"
    source.write_text("content")
    session.override("POST", "Document", 201, {"id": 9, "message": ""})
    assert _connector().upload_document("Report", source) == 9
    request = session.rsps.calls[0].request
    assert b"uploadManifest" in request.body
    assert b'"_filename": ["report.txt"]' in request.body
    assert request.headers["Content-Type"].startswith("multipart/form-data")
    with pytest.raises(ConfigurationError):
        _connector().upload_document("Missing", tmp_path / "missing.txt")


def test_download_document_stays_in_directory(session: GlpiMock, tmp_path: Path) -> None:
    """Download writes inside the target directory only.

    Args:
        session: Simulator with an open session.
        tmp_path: Temporary directory.
    """
    session.override("GET", "Document/9", 200, "file-bytes")
    target = _connector().download_document(9, tmp_path, filename="../escape.txt")
    assert target == tmp_path / "escape.txt"
    assert target.read_text() == "file-bytes"
    with pytest.raises(ConfigurationError):
        _connector().download_document(9, tmp_path / "missing")


def test_kill_session_closes_even_on_error(session: GlpiMock) -> None:
    """The session token is dropped even when killSession fails.

    Args:
        session: Simulator with an open session.
    """
    connector = _connector()
    session.override("GET", "killSession", 401, ["ERROR_SESSION_TOKEN_INVALID", "invalid"])
    with pytest.raises(Exception, match="ERROR_SESSION_TOKEN_INVALID"):
        Glpi.disconnect()
    assert not Glpi.is_connected()
    assert connector._session_token is None
