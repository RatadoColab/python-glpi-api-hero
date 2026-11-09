"""Shared test fixtures: a simulated GLPI 10 legacy REST API and global state reset.

The simulator answers every endpoint used by the library with realistic GLPI 10
bodies (see ``apirest.md`` in the GLPI 10 sources). Scenarios can override single
endpoints with specific responses (errors, partial results, empty lists).
"""

from __future__ import annotations

import json
import re
import zlib
from collections.abc import Iterator
from typing import Any
from urllib.parse import parse_qsl, urlsplit

import pytest
import requests
import responses

BASE_URL = "https://glpi.test/apirest.php"
APP_TOKEN = "test-app-token"
USER_TOKEN = "test-user-token"
USERNAME = "test-user"
PASSWORD = "test-password"
SESSION_TOKEN = "test-session-token"

# Headers that matter for the HTTP contract (other headers depend on requests' version)
CONTRACT_HEADERS = ("App-Token", "Session-Token", "Authorization")

# Endpoints that are not itemtypes
_SPECIAL = {
    "initSession",
    "killSession",
    "changeActiveProfile",
    "changeActiveEntities",
    "getFullSession",
    "getGlpiConfig",
    "getMultipleItems",
    "getMyProfiles",
    "getActiveProfile",
    "getMyEntities",
    "getActiveEntities",
}


def _search_options(itemtype: str) -> dict[str, Any]:
    """Build a small listSearchOptions body for an itemtype.

    Args:
        itemtype: GLPI itemtype name.

    Returns:
        A dict shaped like the GLPI 10 ``listSearchOptions`` answer.
    """
    # Keep the ids used by the library models and a few uid-addressable fields
    return {
        "common": {"name": "Characteristics"},
        "1": {"name": "Name", "table": f"glpi_{itemtype.lower()}s", "field": "name",
              "datatype": "itemlink", "uid": f"{itemtype}.name"},
        "2": {"name": "ID", "table": f"glpi_{itemtype.lower()}s", "field": "id",
              "datatype": "number", "uid": f"{itemtype}.id"},
        "5": {"name": "Serial number", "table": f"glpi_{itemtype.lower()}s", "field": "serial",
              "datatype": "string", "uid": f"{itemtype}.serial"},
        "80": {"name": "Entity", "table": "glpi_entities", "field": "completename",
               "datatype": "dropdown", "uid": f"{itemtype}.Entity.completename"},
    }


class GlpiMock:
    """Router that simulates the GLPI 10 legacy REST API on top of ``responses``.

    Attributes:
        rsps: Active ``responses.RequestsMock``.
        overrides: Specific answers keyed by ``(METHOD, path)``.
    """

    def __init__(self, rsps: responses.RequestsMock) -> None:
        """Register the catch-all callbacks for every HTTP method.

        Args:
            rsps: Active ``responses.RequestsMock`` instance.
        """
        self.rsps = rsps
        self.overrides: dict[tuple[str, str], dict[str, Any]] = {}
        # One catch-all callback per HTTP verb used by the API
        pattern = re.compile(re.escape(BASE_URL) + r"(/.*)?$")
        for method in ("GET", "POST", "PUT", "DELETE"):
            rsps.add_callback(method, pattern, callback=self._dispatch)

    def override(self, method: str, path: str, status: int = 200, body: Any = None,
                 headers: dict[str, str] | None = None, error: str | None = None) -> None:
        """Replace the default answer of one endpoint.

        Args:
            method: HTTP method (``GET``, ``POST``...).
            path: Path relative to ``apirest.php`` (e.g. ``Location/999``).
            status: HTTP status code to answer.
            body: JSON-serializable body, or a ``str`` sent as raw text.
            headers: Extra response headers.
            error: ``"connection"`` to raise a connection error instead of answering.
        """
        self.overrides[(method.upper(), path)] = {
            "status": status, "body": body, "headers": headers or {}, "error": error,
        }

    def reset_calls(self) -> None:
        """Forget the requests captured so far."""
        self.rsps.calls.reset()

    def captured(self) -> list[dict[str, Any]]:
        """Return the captured requests in a stable, comparable form.

        Returns:
            One dict per request with method, path, query, contract headers and body.
        """
        return [describe_request(call.request) for call in self.rsps.calls]

    def _dispatch(self, request: requests.PreparedRequest) -> tuple[int, dict[str, str], str]:
        """Answer one request from the overrides or from the default router.

        Args:
            request: The prepared request intercepted by ``responses``.

        Returns:
            ``(status, headers, body)`` as expected by ``responses`` callbacks.

        Raises:
            requests.exceptions.ConnectionError: When the override simulates a network failure.
        """
        path, query = _split(request.url or "")
        override = self.overrides.get(((request.method or "").upper(), path))
        if override is not None:
            # Simulated network failure
            if override["error"] == "connection":
                raise requests.exceptions.ConnectionError("simulated connection failure")
            return _encode(override["status"], override["body"], override["headers"])
        return self._default(request, path, query)

    def _default(self, request: requests.PreparedRequest, path: str,
                 query: list[tuple[str, str]]) -> tuple[int, dict[str, str], str]:
        """Produce the default GLPI 10 answer for an endpoint.

        Args:
            request: The prepared request.
            path: Path relative to ``apirest.php``.
            query: Parsed query string.

        Returns:
            ``(status, headers, body)``.
        """
        method = (request.method or "").upper()
        parts = [p for p in path.split("/") if p]
        payload = _json_body(request)
        items = payload.get("input", []) if isinstance(payload, dict) else []
        # Session endpoints
        if parts == ["initSession"]:
            return _encode(200, {"session_token": SESSION_TOKEN})
        if parts == ["killSession"]:
            return _encode(200, "")
        if parts in (["changeActiveProfile"], ["changeActiveEntities"]):
            return _encode(200, "")
        if parts == ["getFullSession"]:
            return _encode(200, {"session": {"glpiID": 2, "glpiname": "glpi",
                                             "glpiactiveprofile": {"id": 4, "name": "Super-Admin"},
                                             "glpiactive_entity": 0}})
        if parts == ["getGlpiConfig"]:
            return _encode(200, {"cfg_glpi": {"version": "10.0.26", "url_base": "https://glpi.test"}})
        if parts == ["getMultipleItems"]:
            return _encode(200, [{"id": 1, "name": "item-1"}])
        # Search engine
        if parts[:1] == ["listSearchOptions"] and len(parts) == 2:
            return _encode(200, _search_options(parts[1]))
        if parts[:1] == ["search"] and len(parts) == 2:
            total = zlib.crc32(json.dumps(sorted(query)).encode()) % 40 + 1
            if ("range", "0-0") in query:
                return _encode(200, {"totalcount": total, "count": 0, "data": []},
                               {"Content-Range": f"0-0/{total}"})
            data = [{"1": f"{parts[1]}-1", "2": 1}, {"1": f"{parts[1]}-2", "2": 2}]
            return _encode(200, {"totalcount": 2, "count": 2, "data": data},
                           {"Content-Range": "0-1/2"})
        # Itemtype endpoints
        if len(parts) == 1 and parts[0] not in _SPECIAL:
            return self._collection(method, parts[0], items)
        if len(parts) == 2:
            return self._single(method, parts[0], parts[1])
        if len(parts) == 3:
            return self._sub_items(method, parts[0], parts[1], parts[2], items)
        return _encode(400, ["ERROR_RESOURCE_NOT_FOUND_NOR_COMMONDBTM",
                             "resource not found or not an instance of CommonDBTM"])

    @staticmethod
    def _collection(method: str, itemtype: str, items: list[Any]) -> tuple[int, dict[str, str], str]:
        """Answer the ``<itemtype>`` endpoint (list, add, update, delete).

        Args:
            method: HTTP method.
            itemtype: GLPI itemtype.
            items: ``input`` payload items.

        Returns:
            ``(status, headers, body)``.
        """
        if method == "GET":
            rows = [{"id": 1, "name": f"{itemtype}-1", "entities_id": 0},
                    {"id": 2, "name": f"{itemtype}-2", "entities_id": 0}]
            return _encode(200, rows, {"Content-Range": "0-1/2"})
        if method == "POST":
            created = [{"id": 101 + idx, "message": ""} for idx, _ in enumerate(items)]
            return _encode(201, created)
        # PUT and DELETE answer one status per input item
        done = [{str(_item_id(item)): True, "message": ""} for item in items]
        return _encode(200, done)

    @staticmethod
    def _single(method: str, itemtype: str, item_id: str) -> tuple[int, dict[str, str], str]:
        """Answer the ``<itemtype>/<id>`` endpoint.

        Args:
            method: HTTP method.
            itemtype: GLPI itemtype.
            item_id: Item id taken from the path.

        Returns:
            ``(status, headers, body)``.
        """
        if method == "GET":
            return _encode(200, {"id": int(item_id), "name": f"{itemtype}-{item_id}",
                                 "entities_id": 0, "is_recursive": 0})
        return _encode(200, [{item_id: True, "message": ""}])

    @staticmethod
    def _sub_items(method: str, itemtype: str, item_id: str, sub_itemtype: str,
                   items: list[Any]) -> tuple[int, dict[str, str], str]:
        """Answer the ``<itemtype>/<id>/<sub_itemtype>`` endpoint.

        Args:
            method: HTTP method.
            itemtype: Parent itemtype.
            item_id: Parent id.
            sub_itemtype: Child itemtype.
            items: ``input`` payload items.

        Returns:
            ``(status, headers, body)``.
        """
        if method == "GET":
            rows = [{"id": 11, "itemtype": itemtype, "items_id": int(item_id), "name": f"{sub_itemtype}-11"},
                    {"id": 12, "itemtype": itemtype, "items_id": int(item_id), "name": f"{sub_itemtype}-12"}]
            return _encode(200, rows)
        if method == "POST":
            return _encode(201, [{"id": 201 + idx, "message": ""} for idx, _ in enumerate(items)])
        return _encode(200, [{str(_item_id(item)): True, "message": ""} for item in items])


def _item_id(item: Any) -> Any:
    """Return the ``id`` of an input item, or the item itself when it is not a dict.

    Args:
        item: One element of the ``input`` payload.

    Returns:
        The id used in the per-item status.
    """
    return item.get("id") if isinstance(item, dict) else item


def _encode(status: int, body: Any, headers: dict[str, str] | None = None) -> tuple[int, dict[str, str], str]:
    """Encode a body for a ``responses`` callback.

    Args:
        status: HTTP status code.
        body: JSON-serializable body, or raw text when ``str``.
        headers: Extra headers.

    Returns:
        ``(status, headers, body)``.
    """
    out = {"Content-Type": "application/json; charset=UTF-8", **(headers or {})}
    # Raw text bodies are sent unchanged
    if isinstance(body, str):
        return status, out, body
    return status, out, json.dumps(body)


def _split(url: str) -> tuple[str, list[tuple[str, str]]]:
    """Split an absolute URL into the path relative to ``apirest.php`` and its query.

    Args:
        url: Absolute request URL.

    Returns:
        ``(relative_path, sorted_query_pairs)``.
    """
    parts = urlsplit(url)
    base_path = urlsplit(BASE_URL).path
    path = parts.path[len(base_path):] if parts.path.startswith(base_path) else parts.path
    return path.strip("/"), sorted(parse_qsl(parts.query, keep_blank_values=True))


def _json_body(request: requests.PreparedRequest) -> Any:
    """Decode the JSON body of a request.

    Args:
        request: The prepared request.

    Returns:
        The decoded body, the raw text when it is not JSON, or ``None`` when empty.
    """
    body = request.body
    if not body:
        return None
    # requests may hand bytes or str depending on how the body was built
    text = body.decode() if isinstance(body, bytes) else body
    try:
        return json.loads(text)
    except ValueError:
        return text


def describe_request(request: requests.PreparedRequest) -> dict[str, Any]:
    """Describe a request in the form stored by the characterization fixture.

    Args:
        request: The prepared request.

    Returns:
        Dict with ``method``, ``path``, ``query``, ``headers`` and ``body``.
    """
    path, query = _split(request.url or "")
    headers = {name: request.headers[name] for name in CONTRACT_HEADERS if name in request.headers}
    return {
        "method": (request.method or "").upper(),
        "path": path,
        "query": {key: value for key, value in query},
        "headers": headers,
        "body": _json_body(request),
    }


def reset_api_state() -> None:
    """Reset the global session state kept by the library between tests."""
    # Imported lazily so the simulator stays usable if the package layout changes
    from glpi_api_hero import ApiCommunication

    ApiCommunication.ERROR = ""
    ApiCommunication.glpi = None
    ApiCommunication.logged_user = None
    ApiCommunication.glpi_connection = {"url": "", "apptoken": "", "usertoken": "",
                                        "user": None, "passwd": None}
    ApiCommunication.glpi_environment = {"profiles_id": None, "entities_id": None,
                                         "is_recursive": True}
    ApiCommunication.last_glpi_environment = {"profiles_id": -1, "entities_id": -1,
                                              "is_recursive": None}


def mocked_glpi() -> Iterator[GlpiMock]:
    """Activate the simulator and yield its router (usable outside pytest).

    Yields:
        The active ``GlpiMock``.
    """
    with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
        yield GlpiMock(rsps)


@pytest.fixture(autouse=True)
def _clean_api_state() -> Iterator[None]:
    """Reset the library global state before and after every test."""
    reset_api_state()
    yield
    reset_api_state()


@pytest.fixture
def glpi_mock() -> Iterator[GlpiMock]:
    """Provide an active GLPI 10 simulator.

    Yields:
        The active ``GlpiMock``.
    """
    yield from mocked_glpi()
