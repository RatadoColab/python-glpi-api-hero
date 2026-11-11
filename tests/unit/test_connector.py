"""Legacy REST connector: transport details reproduced from the former glpi-api client."""

from __future__ import annotations

import logging
from pathlib import Path

import pytest
import requests

from glpi_api_hero import Glpi
from glpi_api_hero.core.legacy_rest import LegacyRestConnector
from glpi_api_hero.core.types import OperationResult
from glpi_api_hero.exceptions import (
    AuthenticationError,
    BadRequestError,
    ConfigurationError,
    GlpiAPIError,
    GlpiConnectionError,
    PartialOperationError,
)
from tests.conftest import APP_TOKEN, BASE_URL, SESSION_TOKEN, USER_TOKEN, GlpiMock


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
    """Single quotes are sent as typed (GLPI 10); criteria lists are not modified.

    Args:
        session: Simulator with an open session.
    """
    criteria = [{"field": 1, "searchtype": "equals", "value": "o'neil"}]
    meta = [{"link": "AND", "itemtype": "Monitor", "field": 1, "searchtype": "contains", "value": "m"}]
    snapshot = (repr(criteria), repr(meta))
    _connector().search("User", criteria, metacriteria=meta)
    query = session.captured()[0]["query"]
    assert query["criteria[0][value]"] == "o'neil"
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
    session.override("GET", "Document/9", 200, "file-bytes",
                     headers={"Content-Disposition": 'attachment; filename="../report.pdf"'})
    target = _connector().download_document(9, tmp_path, filename="../escape.txt")
    assert target == tmp_path / "escape.txt"
    assert target.read_text() == "file-bytes"
    # Without a name, one request is enough: the name comes from Content-Disposition
    session.reset_calls()
    assert _connector().download_document(9, tmp_path) == tmp_path / "report.pdf"
    assert [request["path"] for request in session.captured()] == ["Document/9"]
    with pytest.raises(ConfigurationError):
        _connector().download_document(9, tmp_path / "missing")


@pytest.mark.parametrize(("header", "expected"), [
    ("attachment; filename=\"..\"", "document-9"),
    ("attachment; filename=\".\"", "document-9"),
    ("attachment; filename=\"C:evil.txt\"", "evil.txt"),
    ("attachment; filename=\"a\\\\b\\\\..\\\\c.txt\"", "c.txt"),
    ("attachment; filename=\"d\\'Ar\\\"t.txt\"", "d'Ar\"t.txt"),
    ("attachment; filename=\"caf\xe9.txt\"; filename*=utf-8''caf%C3%A9%3B%27x.txt", "caf\xe9;'x.txt"),
])
def test_download_filename_from_content_disposition(session: GlpiMock, tmp_path: Path, header: str,
                                                    expected: str) -> None:
    """The name comes from the RFC 5987 form when present and never points at a directory.

    Args:
        session: Simulator with an open session.
        tmp_path: Temporary directory.
        header: Content-Disposition value.
        expected: Expected file name.
    """
    session.override("GET", "Document/9", 200, "bytes", headers={"Content-Disposition": header})
    assert _connector().download_document(9, tmp_path) == tmp_path / expected
    assert (tmp_path / expected).read_text() == "bytes"


def test_download_failure_leaves_no_partial_file(session: GlpiMock, tmp_path: Path,
                                                 monkeypatch: pytest.MonkeyPatch) -> None:
    """A network error while streaming becomes ``GlpiConnectionError`` and keeps the previous file.

    Args:
        session: Simulator with an open session.
        tmp_path: Temporary directory.
        monkeypatch: Pytest monkeypatch.
    """
    existing = tmp_path / "report.pdf"
    existing.write_text("old")
    session.override("GET", "Document/9", 200, "new-bytes",
                     headers={"Content-Disposition": 'attachment; filename="report.pdf"'})

    def broken(self: requests.Response, *args: object, **kwargs: object) -> object:
        """Fail in the middle of the transfer."""
        yield b"ne"
        raise requests.exceptions.ChunkedEncodingError("connection broken")

    monkeypatch.setattr(requests.Response, "iter_content", broken)
    with pytest.raises(GlpiConnectionError):
        _connector().download_document(9, tmp_path, overwrite=True)
    assert existing.read_text() == "old"
    assert [path.name for path in tmp_path.iterdir()] == ["report.pdf"]


def test_upload_error_survives_a_failed_purge(session: GlpiMock, tmp_path: Path) -> None:
    """When the purge of the empty Document fails too, the upload error is still the one raised.

    Args:
        session: Simulator with an open session.
        tmp_path: Temporary directory.
    """
    source = tmp_path / "virus.exe"
    source.write_text("x")
    session.override("POST", "Document", 201, {"id": 55, "upload_result": {"filename": [
        {"name": "virus.exe", "error": "Filetype not allowed"}]}})
    session.override("DELETE", "Document", 429, ["ERROR_RATE_LIMIT", "slow down"])
    with pytest.raises(BadRequestError, match="Filetype not allowed"):
        _connector().upload_document("Bad", source)


def test_relative_ca_bundle_is_stored_absolute(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A relative CA bundle path keeps pointing at the same file after a chdir.

    Args:
        tmp_path: Temporary directory.
        monkeypatch: Pytest monkeypatch.
    """
    (tmp_path / "ca.pem").write_text("pem")
    monkeypatch.chdir(tmp_path)
    connector = LegacyRestConnector(BASE_URL, user_token=USER_TOKEN, verify="ca.pem")
    assert connector.verify == str(tmp_path / "ca.pem")


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


def test_upload_error_purges_the_empty_document(session: GlpiMock, tmp_path: Path) -> None:
    """A refused file leaves no empty Document behind.

    Args:
        session: Simulator with an open session.
        tmp_path: Temporary directory.
    """
    source = tmp_path / "virus.exe"
    source.write_text("x")
    session.override("POST", "Document", 201, {"id": 55, "upload_result": {"filename": [
        {"name": "virus.exe", "error": "Filetype not allowed"}]}})
    with pytest.raises(BadRequestError, match="Filetype not allowed") as info:
        _connector().upload_document("Bad", source)
    assert info.value.error_code == "ERROR_GLPI_INVALID_DOCUMENT"
    purge = session.captured()[-1]
    assert (purge["method"], purge["path"], purge["query"]) == ("DELETE", "Document", {"force_purge": "true"})
    assert purge["body"] == {"input": [{"id": 55}]}


def test_results_are_reconciled_with_sent_ids(session: GlpiMock) -> None:
    """Ids without a result (GLPI skips missing items on update) are reported as failed.

    Args:
        session: Simulator with an open session.
    """
    session.override("PUT", "Location", 207, ["ERROR_GLPI_PARTIAL_UPDATE", [{"1": True, "message": ""}]])
    with pytest.raises(PartialOperationError) as info:
        _connector().update_items("Location", [{"id": 1}, {"id": 999}])
    assert info.value.results == [OperationResult(1, True), OperationResult(999, False, "Item not found")]
    assert "1 of 2 items failed" in str(info.value)


def test_non_json_answers_stay_in_the_hierarchy(session: GlpiMock, glpi_mock: GlpiMock) -> None:
    """HTML or PHP warnings instead of JSON raise ``GlpiAPIError``.

    Args:
        session: Simulator with an open session.
        glpi_mock: Same simulator (used for a new login).
    """
    session.override("PUT", "Location", 200, "<html>proxy</html>")
    with pytest.raises(GlpiAPIError, match="invalid JSON"):
        _connector().update_items("Location", [{"id": 1}])
    glpi_mock.override("GET", "initSession", 200, "<html>login page</html>")
    with pytest.raises(GlpiAPIError):
        Glpi.connect(BASE_URL, APP_TOKEN, user_token=USER_TOKEN)


def test_exceptions_do_not_keep_credentials(glpi_mock: GlpiMock) -> None:
    """The response kept by an exception has its credential headers masked.

    Args:
        glpi_mock: Active GLPI simulator.
    """
    glpi_mock.override("GET", "initSession", 401, ["ERROR_GLPI_LOGIN", "refused"])
    with pytest.raises(AuthenticationError) as info:
        Glpi.connect(BASE_URL, APP_TOKEN, user_token=USER_TOKEN)
    headers = info.value.response.request.headers
    assert headers["Authorization"] == "***"
    assert headers["App-Token"] == "***"
    # The request recorded by the transport itself is untouched
    assert glpi_mock.captured()[0]["headers"]["Authorization"] == f"user_token {USER_TOKEN}"


def test_connection_error_cause_is_masked(session: GlpiMock, monkeypatch: pytest.MonkeyPatch) -> None:
    """The chained requests exception does not expose the credentials (request, response, history, message).

    Args:
        session: Simulator with an open session.
        monkeypatch: Pytest monkeypatch.
    """
    connector = _connector()
    secret_request = requests.Request("GET", f"{BASE_URL}/Location/1",
                                      headers={"Session-Token": SESSION_TOKEN, "App-Token": APP_TOKEN}).prepare()
    previous = requests.Response()
    previous.request = secret_request
    response = requests.Response()
    response.status_code = 302
    response.request = secret_request
    response.history = [previous]

    def fail(*args: object, **kwargs: object) -> object:
        """Raise what requests raises on a redirect loop, with the token in the message."""
        raise requests.exceptions.TooManyRedirects(f"loop with {SESSION_TOKEN}", request=secret_request,
                                                   response=response)

    monkeypatch.setattr(connector._http, "request", fail)
    with pytest.raises(GlpiConnectionError) as info:
        connector.get_item("Location", 1)
    cause = info.value.__cause__
    assert SESSION_TOKEN not in str(info.value) and SESSION_TOKEN not in str(cause)
    for request in (cause.request, cause.response.request, cause.response.history[0].request):
        assert request.headers["Session-Token"] == "***"
        assert request.headers["App-Token"] == "***"
    # The original prepared request is left untouched
    assert secret_request.headers["Session-Token"] == SESSION_TOKEN


def test_redact_covers_repr_and_basic_forms() -> None:
    """Tokens with whitespace are masked in their ``repr()`` form, and so is the Basic credential."""
    connector = LegacyRestConnector(BASE_URL, "app", username="user", password="pa ss\n")
    shown = repr("pa ss\n")[1:-1]
    assert "pa ss" not in connector._redact(f"Invalid header value {shown}")
    assert "dXNlcjpwYSBzcwo=" not in connector._redact("Basic dXNlcjpwYSBzcwo=")


def test_verify_overrides_environment_bundle(glpi_mock: GlpiMock, monkeypatch: pytest.MonkeyPatch) -> None:
    """The TLS setting is sent with every request, so REQUESTS_CA_BUNDLE cannot replace False.

    Args:
        glpi_mock: Active GLPI simulator.
        monkeypatch: Pytest monkeypatch.
    """
    monkeypatch.setenv("REQUESTS_CA_BUNDLE", "/etc/ssl/certs/other.pem")
    Glpi.connect(BASE_URL, user_token=USER_TOKEN, verify_tls=False)
    seen = []
    original = _connector()._http.request

    def spy(*args: object, **kwargs: object) -> object:
        """Record the TLS setting before sending."""
        seen.append(kwargs.get("verify"))
        return original(*args, **kwargs)

    monkeypatch.setattr(_connector()._http, "request", spy)
    _connector().get_config()
    assert seen == [False]


def test_metacriteria_fields_use_their_itemtype(session: GlpiMock) -> None:
    """A uid in a meta criterion is resolved with the meta itemtype.

    Args:
        session: Simulator with an open session.
    """
    _connector().search("User", [], metacriteria=[{"link": "AND", "itemtype": "Monitor", "field": "serial",
                                                   "searchtype": "contains", "value": "m"}])
    paths = [request["path"] for request in session.captured()]
    assert paths == ["listSearchOptions/Monitor", "search/User"]
    assert session.captured()[1]["query"]["criteria[0][field]"] == "5"


def test_update_without_id_is_refused_before_any_request(session: GlpiMock) -> None:
    """GLPI skips update items without ``id`` and answers 200, so the library refuses them.

    Args:
        session: Simulator with an open session.
    """
    session.reset_calls()
    with pytest.raises(BadRequestError, match="id"):
        _connector().update_items("Location", [{"id": 1, "name": "a"}, {"name": "b"}])
    with pytest.raises(BadRequestError, match="id"):
        _connector().update_sub_items("Computer", 3, "Infocom", [{"value": 1}])
    assert session.captured() == []


def test_search_extra_booleans_are_sent_as_lowercase_text(session: GlpiMock) -> None:
    """Boolean keyword arguments of ``search`` use ``true``/``false``, like the other reads.

    Args:
        session: Simulator with an open session.
    """
    session.reset_calls()
    _connector().search("Computer", [], expand_dropdowns=False, is_deleted=True)
    query = session.captured()[0]["query"]
    assert (query["expand_dropdowns"], query["is_deleted"]) == ("false", "true")


def test_downloaded_file_is_owner_only_unless_asked(session: GlpiMock, tmp_path: Path) -> None:
    """Downloads are created with mode 0600 by default; ``mode`` opts into wider permissions (umask applies).

    Args:
        session: Simulator with an open session.
        tmp_path: Temporary directory.
    """
    import os

    session.override("GET", "Document/9", 200, "bytes", headers={"Content-Disposition": 'attachment; filename="a.txt"'})
    previous = os.umask(0o022)
    try:
        private = _connector().download_document(9, tmp_path)
        shared = _connector().download_document(9, tmp_path, "b.txt", mode=0o666)
    finally:
        os.umask(previous)
    assert private.stat().st_mode & 0o777 == 0o600
    assert shared.stat().st_mode & 0o777 == 0o644


@pytest.mark.parametrize("segment", ["..", ".", ""])
def test_dot_and_empty_path_segments_are_refused(session: GlpiMock, segment: str) -> None:
    """A segment that would change the endpoint reached by the request is never sent.

    Args:
        session: Simulator with an open session.
        segment: Dangerous path segment.
    """
    session.reset_calls()
    with pytest.raises(BadRequestError, match="invalid path segment"):
        _connector().get_sub_items("Computer", 3, segment)
    assert session.captured() == []


def test_path_segments_are_percent_encoded(session: GlpiMock) -> None:
    """Slashes inside a segment stay inside it.

    Args:
        session: Simulator with an open session.
    """
    session.reset_calls()
    _connector().get_sub_items("Computer", 3, "User/1")
    assert session.rsps.calls[0].request.url.split("?")[0].endswith("/Computer/3/User%2F1")


def test_download_does_not_overwrite_without_the_flag(session: GlpiMock, tmp_path: Path) -> None:
    """An existing file is kept (``FileExistsError``) unless ``overwrite=True``; no temporary file is left."""
    target = tmp_path / "report.pdf"
    target.write_text("old")
    session.override("GET", "Document/9", 200, "new",
                     headers={"Content-Disposition": 'attachment; filename="report.pdf"'})
    with pytest.raises(FileExistsError):
        _connector().download_document(9, tmp_path)
    assert target.read_text() == "old"
    assert [path.name for path in tmp_path.iterdir()] == ["report.pdf"]
    assert _connector().download_document(9, tmp_path, overwrite=True) == target
    assert target.read_text() == "new"
    assert [path.name for path in tmp_path.iterdir()] == ["report.pdf"]


def test_download_refuses_a_symlink_that_leaves_the_directory(session: GlpiMock, tmp_path: Path) -> None:
    """A planted symlink with the target name cannot redirect the write outside the directory."""
    outside = tmp_path / "outside"
    outside.mkdir()
    directory = tmp_path / "dest"
    directory.mkdir()
    (directory / "report.pdf").symlink_to(outside / "secret.txt")
    session.override("GET", "Document/9", 200, "new",
                     headers={"Content-Disposition": 'attachment; filename="report.pdf"'})
    with pytest.raises(FileExistsError):
        _connector().download_document(9, directory)
    assert not (outside / "secret.txt").exists()
    # With overwrite the link itself is replaced (never followed): nothing is written outside
    target = _connector().download_document(9, directory, overwrite=True)
    assert not target.is_symlink()
    assert not (outside / "secret.txt").exists()


def test_download_filename_drops_control_characters(session: GlpiMock, tmp_path: Path) -> None:
    """Control characters of a server-provided name are removed."""
    session.override("GET", "Document/9", 200, "x",
                     headers={"Content-Disposition": 'attachment; filename="a\x01b\x7fc.txt"'})
    assert _connector().download_document(9, tmp_path).name == "abc.txt"
