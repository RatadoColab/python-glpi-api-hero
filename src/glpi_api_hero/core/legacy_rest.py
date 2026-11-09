"""Connector for the legacy GLPI REST API (``apirest.php``, GLPI 9.5 to 12)."""

from __future__ import annotations

import base64
import json
import logging
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import Any

import requests

from glpi_api_hero.core.connector import Connector
from glpi_api_hero.core.types import OperationResult
from glpi_api_hero.exceptions import (
    ConfigurationError,
    GlpiAPIError,
    GlpiConnectionError,
    PartialOperationError,
    RateLimitError,
    error_class_for,
)

logger = logging.getLogger("glpi_api_hero")

DEFAULT_TIMEOUT = 30.0


def _convert_bools(params: dict[str, Any]) -> dict[str, Any]:
    """Render booleans as ``"true"``/``"false"``, as expected by the legacy API.

    Args:
        params: Query parameters.

    Returns:
        A new dict with converted booleans.
    """
    return {key: str(value).lower() if isinstance(value, bool) else value for key, value in params.items()}


def _expand_search_text(params: dict[str, Any]) -> dict[str, Any]:
    """Turn ``searchText={"name": "x"}`` into ``searchText[name]=x``.

    Args:
        params: Query parameters.

    Returns:
        A new dict with the expanded ``searchText``.

    Raises:
        TypeError: When ``searchText`` is not a dict.
    """
    out = dict(params)
    search_text = out.pop("searchText", None)
    if search_text is None:
        return out
    if not isinstance(search_text, dict):
        raise TypeError(f"searchText must be a dict, got {type(search_text).__name__}")
    out.update({f"searchText[{key}]": value for key, value in search_text.items()})
    return out


class LegacyRestConnector(Connector):
    """Connector over ``requests`` for the legacy ``apirest.php`` endpoint.

    Attributes:
        url: Base URL of ``apirest.php``.
        timeout: Timeout in seconds applied to every request.
    """

    def __init__(self, url: str, app_token: str | None = None, *, user_token: str | None = None,
                 username: str | None = None, password: str | None = None, verify: bool | str = True,
                 timeout: float = DEFAULT_TIMEOUT) -> None:
        """Prepare the connector (no request is sent until :meth:`init_session`).

        Args:
            url: Base URL of ``apirest.php`` (e.g. ``https://glpi.example/apirest.php``).
            app_token: Application token, when the API client requires one.
            user_token: User API token (used when no username is given).
            username: Login for Basic authentication.
            password: Password for Basic authentication.
            verify: ``True`` to verify TLS, ``False`` to skip it, or a CA bundle path.
            timeout: Timeout in seconds of every request.

        Raises:
            ConfigurationError: When the URL or the credentials are missing.
        """
        super().__init__()
        if not url:
            raise ConfigurationError("the GLPI API URL is required")
        if not username and not user_token:
            raise ConfigurationError("a user token or a username and password are required")
        if username and password is None:
            raise ConfigurationError("a password is required with a username")
        self.url = url.rstrip("/")
        self.timeout = timeout
        self._app_token = app_token
        self._user_token = user_token
        self._username = username
        self._password = password
        self._session_token: str | None = None
        self._http = requests.Session()
        self._http.verify = verify

    # ------------------------------------------------------------- transport
    @property
    def verify(self) -> bool | str:
        """TLS verification setting of the HTTP session.

        Returns:
            ``True``, ``False`` or the CA bundle path.
        """
        return self._http.verify

    def _redact(self, text: str) -> str:
        """Remove every known secret from a text.

        Args:
            text: Text that may contain secrets.

        Returns:
            The text with secrets replaced by ``***``.
        """
        for secret in (self._app_token, self._user_token, self._password, self._session_token):
            if secret:
                text = text.replace(secret, "***")
        return text

    def _endpoint(self, *parts: Any) -> str:
        """Build the absolute URL of an endpoint.

        Args:
            *parts: Path segments.

        Returns:
            The URL.
        """
        return "/".join([self.url, *(str(part) for part in parts)])

    def _send(self, method: str, parts: Iterable[Any], *, params: Any = None, body: Any = None,
              headers: dict[str, Any] | None = None, files: Any = None, data: Any = None) -> requests.Response:
        """Send one HTTP request, wrapping network errors.

        Args:
            method: HTTP method.
            parts: Endpoint path segments.
            params: Query parameters.
            body: JSON body.
            headers: Per-request headers.
            files: Multipart files.
            data: Multipart form fields.

        Returns:
            The HTTP response.

        Raises:
            GlpiConnectionError: On network, TLS or timeout errors.
        """
        url = self._endpoint(*parts)
        try:
            response = self._http.request(method, url, params=params, json=body, headers=headers, files=files,
                                          data=data, timeout=self.timeout)
        except requests.exceptions.RequestException as exc:
            raise GlpiConnectionError(self._redact(f"communication error: {exc}")) from exc
        logger.debug("%s %s -> %s", method, "/".join(str(p) for p in parts), response.status_code)
        if "Content-Range" in response.headers:
            logger.debug("Content-Range: %s", response.headers["Content-Range"])
        return response

    def _error(self, response: requests.Response) -> GlpiAPIError | PartialOperationError:
        """Build the exception that matches an error response.

        Args:
            response: HTTP response with an error status.

        Returns:
            The exception to raise.
        """
        error_code: str | None = None
        detail: Any = None
        try:
            payload = response.json()
        except ValueError:
            payload = None
        # GLPI errors are ["ERROR_KEY", message-or-results]
        if isinstance(payload, list) and payload and isinstance(payload[0], str) and payload[0].startswith("ERROR"):
            error_code = payload[0]
            detail = payload[1] if len(payload) > 1 else ""
        if isinstance(detail, list):
            # Bulk write where every item failed: per-item results instead of a message
            results = _parse_results(detail)
            return PartialOperationError(self._redact(f"({error_code}) {_summary(results)}"), results,
                                         error_code=error_code)
        if error_code is not None:
            message = detail if isinstance(detail, str) else json.dumps(detail)
        else:
            message = f"[{response.status_code}/{response.reason}] {response.text[:500]}".rstrip()
        cls = error_class_for(response.status_code, error_code)
        kwargs: dict[str, Any] = {"status_code": response.status_code, "error_code": error_code, "response": response}
        if cls is RateLimitError:
            kwargs["retry_after"] = _retry_after(response.headers.get("Retry-After"))
        return cls(self._redact(message), **kwargs)

    def _call(self, method: str, parts: Iterable[Any], *, ok: Sequence[int] = (200,), **kwargs: Any) -> Any:
        """Send a request and decode its JSON body, raising on error statuses.

        Args:
            method: HTTP method.
            parts: Endpoint path segments.
            ok: Accepted status codes.
            **kwargs: Arguments of :meth:`_send`.

        Returns:
            The decoded JSON body, the raw text when it is not JSON, or ``None`` when empty.

        Raises:
            GlpiAPIError: On error statuses.
            PartialOperationError: On bulk writes where items failed.
        """
        response = self._send(method, parts, **kwargs)
        if response.status_code not in ok:
            raise self._error(response)
        if not response.content:
            return None
        try:
            return response.json()
        except ValueError:
            return response.text

    def _write(self, method: str, parts: Iterable[Any], items: Sequence[Any],
               params: dict[str, Any] | None = None) -> list[OperationResult]:
        """Send a bulk write and normalize the per-item results.

        Args:
            method: ``POST``, ``PUT`` or ``DELETE``.
            parts: Endpoint path segments.
            items: ``input`` payload.
            params: Query parameters.

        Returns:
            One result per item.

        Raises:
            PartialOperationError: When GLPI answers 207 (some items failed).
        """
        response = self._send(method, parts, params=params, body={"input": list(items)})
        if response.status_code == 207:
            payload = response.json()
            results = _parse_results(payload[1] if isinstance(payload, list) and len(payload) > 1 else [])
            error_code = payload[0] if isinstance(payload, list) and payload else None
            raise PartialOperationError(self._redact(f"({error_code}) {_summary(results)}"), results,
                                        error_code=error_code)
        if response.status_code not in (200, 201, 204):
            raise self._error(response)
        if not response.content:
            # 204 without body: every item succeeded
            return [OperationResult(id=_input_id(item), ok=True) for item in items]
        return _parse_results(response.json())

    # --------------------------------------------------------------- session
    def init_session(self) -> None:
        """Open the session with the user token or with Basic authentication.

        Raises:
            AuthenticationError: When the credentials are refused.
            GlpiConnectionError: When the server cannot be reached.
        """
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if self._app_token:
            headers["App-Token"] = self._app_token
        if self._username:
            raw = f"{self._username}:{self._password}".encode()
            headers["Authorization"] = "Basic " + base64.b64encode(raw).decode()
        else:
            headers["Authorization"] = f"user_token {self._user_token}"
        body = self._call("GET", ["initSession"], headers=headers, params={})
        self._session_token = body["session_token"]
        # Headers sent by every later request
        session_headers = {"Content-Type": "application/json", "Session-Token": self._session_token}
        if self._app_token:
            session_headers["App-Token"] = self._app_token
        self._http.headers.update(session_headers)

    def kill_session(self) -> None:
        """Close the session on the server and release the HTTP connections."""
        try:
            if self._session_token:
                self._call("GET", ["killSession"])
        finally:
            self._session_token = None
            self._http.close()

    def get_my_profiles(self) -> list[dict[str, Any]]:
        """Return the profiles of the logged user.

        Returns:
            The profiles.
        """
        return self._call("GET", ["getMyProfiles"]).get("myprofiles", [])

    def get_active_profile(self) -> dict[str, Any]:
        """Return the active profile.

        Returns:
            The profile.
        """
        return self._call("GET", ["getActiveProfile"]).get("active_profile", {})

    def set_active_profile(self, profiles_id: int) -> None:
        """Change the active profile.

        Args:
            profiles_id: Profile id.
        """
        self._call("POST", ["changeActiveProfile"], body={"profiles_id": profiles_id})

    def get_my_entities(self, is_recursive: bool = False) -> list[dict[str, Any]]:
        """Return the entities reachable by the logged user.

        Args:
            is_recursive: Include sub-entities.

        Returns:
            The entities.
        """
        params = _convert_bools({"is_recursive": is_recursive})
        return self._call("GET", ["getMyEntities"], params=params).get("myentities", [])

    def get_active_entities(self) -> dict[str, Any]:
        """Return the active entities.

        Returns:
            The active entity data.
        """
        return self._call("GET", ["getActiveEntities"]).get("active_entity", {})

    def set_active_entities(self, entities_id: int, is_recursive: bool = False) -> None:
        """Change the active entity.

        Args:
            entities_id: Entity id.
            is_recursive: Also activate the sub-entities.
        """
        self._call("POST", ["changeActiveEntities"], body={"entities_id": entities_id, "is_recursive": is_recursive})

    def get_full_session(self) -> dict[str, Any]:
        """Return the server-side session data.

        Returns:
            The ``session`` object.
        """
        return self._call("GET", ["getFullSession"])["session"]

    def get_config(self) -> dict[str, Any]:
        """Return the GLPI configuration.

        Returns:
            The configuration body.
        """
        return self._call("GET", ["getGlpiConfig"])

    # ----------------------------------------------------------------- reads
    def get_item(self, itemtype: str, items_id: int, **params: Any) -> dict[str, Any]:
        """Return one item.

        Args:
            itemtype: GLPI itemtype.
            items_id: Item id.
            **params: Extra API parameters.

        Returns:
            The item fields.

        Raises:
            NotFoundError: When the item does not exist.
        """
        return self._call("GET", [itemtype, items_id], params=_convert_bools(params))

    def get_all_items(self, itemtype: str, **params: Any) -> list[dict[str, Any]]:
        """Return the items of an itemtype.

        Args:
            itemtype: GLPI itemtype.
            **params: Extra API parameters.

        Returns:
            The items (empty list when there is none).
        """
        body = self._call("GET", [itemtype], ok=(200, 206), params=_convert_bools(_expand_search_text(params)))
        return body if isinstance(body, list) else []

    def get_sub_items(self, itemtype: str, items_id: int, sub_itemtype: str, **params: Any) -> list[dict[str, Any]]:
        """Return the sub-items of one item.

        Args:
            itemtype: Parent itemtype.
            items_id: Parent id.
            sub_itemtype: Child itemtype.
            **params: Extra API parameters.

        Returns:
            The sub-items (empty list when there is none).
        """
        body = self._call("GET", [itemtype, items_id, sub_itemtype], ok=(200, 206), params=_convert_bools(params))
        return body if isinstance(body, list) else []

    def get_multiple_items(self, refs: Sequence[tuple[str, int]], **params: Any) -> list[dict[str, Any]]:
        """Return several items of possibly different itemtypes.

        Args:
            refs: ``(itemtype, id)`` pairs.
            **params: Extra API parameters.

        Returns:
            The items, in the order of ``refs``.
        """
        query = _convert_bools(params)
        for idx, (itemtype, items_id) in enumerate(refs):
            query[f"items[{idx}][itemtype]"] = itemtype
            query[f"items[{idx}][items_id]"] = items_id
        body = self._call("GET", ["getMultipleItems"], params=query)
        return body if isinstance(body, list) else []

    def list_search_options(self, itemtype: str, raw: bool = False) -> dict[str, Any]:
        """Return the search options of an itemtype.

        Args:
            itemtype: GLPI itemtype.
            raw: Return the options as provided by the GLPI core.

        Returns:
            Search options indexed by field id.
        """
        return self._call("GET", ["listSearchOptions", itemtype], params="raw" if raw else None)

    def _criteria_params(self, itemtype: str, criteria: Sequence[dict[str, Any]],
                         parent: str | None = None) -> dict[str, Any]:
        """Flatten (nested) criteria into ``criteria[i][key]`` parameters.

        Args:
            itemtype: GLPI itemtype (used to translate field uids).
            criteria: Criteria list.
            parent: Key prefix of the enclosing criterion.

        Returns:
            Query parameters.

        Raises:
            TypeError: When ``criteria`` is not a list or tuple.
        """
        if not isinstance(criteria, (list, tuple)):
            raise TypeError(f"search criteria must be a list, got {type(criteria).__name__}")
        params: dict[str, Any] = {}
        for idx, criterion in enumerate(criteria):
            key = f"criteria[{idx}]" if parent is None else f"{parent}[criteria][{idx}]"
            params.update(self._criteria_params(itemtype, criterion.get("criteria", []), key))
            for name, value in criterion.items():
                if name == "criteria":
                    continue
                if name == "field":
                    value = self.field_id(itemtype, value)
                elif isinstance(value, str):
                    # Single quotes are doubled, as the legacy search engine expects
                    value = value.replace("'", "''")
                params[f"{key}[{name}]"] = value
        return params

    def _search_params(self, itemtype: str, criteria: Sequence[dict[str, Any]] | None,
                       forcedisplay: Sequence[int | str] | None, metacriteria: Sequence[dict[str, Any]] | None,
                       params: dict[str, Any]) -> dict[str, Any]:
        """Build the query of a search request (without mutating the inputs).

        Args:
            itemtype: GLPI itemtype.
            criteria: Search criteria.
            forcedisplay: Fields to include.
            metacriteria: Criteria on linked itemtypes.
            params: Extra API parameters.

        Returns:
            Query parameters.
        """
        query: dict[str, Any] = {}
        for idx, field in enumerate(forcedisplay or []):
            query[f"forcedisplay[{idx}]"] = self.field_id(itemtype, field)
        if criteria is not None and not isinstance(criteria, (list, tuple)):
            raise TypeError(f"search criteria must be a list, got {type(criteria).__name__}")
        all_criteria = list(criteria or [])
        all_criteria += [{**criterion, "meta": True} for criterion in (metacriteria or [])]
        query.update(self._criteria_params(itemtype, all_criteria))
        query.update(params)
        return query

    def search_body(self, itemtype: str, criteria: Sequence[dict[str, Any]] | None = None, *,
                    forcedisplay: Sequence[int | str] | None = None,
                    metacriteria: Sequence[dict[str, Any]] | None = None, **params: Any) -> dict[str, Any]:
        """Run the search engine and return the whole legacy body (``totalcount``, ``count``, ``data``).

        Specific to the legacy API; models use :meth:`search`.

        Args:
            itemtype: GLPI itemtype.
            criteria: Search criteria.
            forcedisplay: Fields to include.
            metacriteria: Criteria on linked itemtypes.
            **params: Extra API parameters.

        Returns:
            The decoded body.
        """
        query = self._search_params(itemtype, criteria, forcedisplay, metacriteria, params)
        body = self._call("GET", ["search", itemtype], ok=(200, 206), params=query)
        return body if isinstance(body, dict) else {}

    def search(self, itemtype: str, criteria: Sequence[dict[str, Any]] | None = None, *,
               forcedisplay: Sequence[int | str] | None = None,
               metacriteria: Sequence[dict[str, Any]] | None = None, **params: Any) -> list[dict[str, Any]]:
        """Run the search engine.

        Args:
            itemtype: GLPI itemtype.
            criteria: Search criteria; ``field`` accepts a field id or uid.
            forcedisplay: Fields (id or uid) to include in each row.
            metacriteria: Criteria on linked itemtypes.
            **params: Extra API parameters.

        Returns:
            Rows indexed by field id (as string); empty list when nothing matches.
        """
        body = self.search_body(itemtype, criteria, forcedisplay=forcedisplay, metacriteria=metacriteria, **params)
        data = body.get("data", [])
        # Some GLPI versions index rows by item id
        if isinstance(data, dict):
            return list(data.values())
        return data if isinstance(data, list) else []

    # ---------------------------------------------------------------- writes
    def add_items(self, itemtype: str, items: Sequence[dict[str, Any]]) -> list[OperationResult]:
        """Create items.

        Args:
            itemtype: GLPI itemtype.
            items: Field values of each item.

        Returns:
            One result per item (``id`` is the created id).
        """
        return self._write("POST", [itemtype], items)

    def update_items(self, itemtype: str, items: Sequence[dict[str, Any]]) -> list[OperationResult]:
        """Update items (each one carries its ``id``).

        Args:
            itemtype: GLPI itemtype.
            items: Field values of each item, with ``id``.

        Returns:
            One result per item.
        """
        return self._write("PUT", [itemtype], items)

    def delete_items(self, itemtype: str, ids: Sequence[int], *, force_purge: bool = False,
                     history: bool = True) -> list[OperationResult]:
        """Delete (or purge) items.

        Args:
            itemtype: GLPI itemtype.
            ids: Ids of the items.
            force_purge: Purge instead of moving to the trash bin.
            history: Keep the deletion in the history.

        Returns:
            One result per item.
        """
        params: dict[str, Any] = {}
        # Only non-default flags are sent
        if force_purge:
            params["force_purge"] = True
        if not history:
            params["history"] = False
        return self._write("DELETE", [itemtype], [{"id": items_id} for items_id in ids], _convert_bools(params))

    def add_sub_items(self, itemtype: str, items_id: int, sub_itemtype: str,
                      items: Sequence[dict[str, Any]]) -> list[OperationResult]:
        """Create sub-items under one item.

        Args:
            itemtype: Parent itemtype.
            items_id: Parent id.
            sub_itemtype: Child itemtype.
            items: Field values of each child.

        Returns:
            One result per child.
        """
        return self._write("POST", [itemtype, items_id, sub_itemtype], items)

    def update_sub_items(self, itemtype: str, items_id: int, sub_itemtype: str,
                         items: Sequence[dict[str, Any]]) -> list[OperationResult]:
        """Update sub-items under one item.

        Args:
            itemtype: Parent itemtype.
            items_id: Parent id.
            sub_itemtype: Child itemtype.
            items: Field values of each child, with ``id``.

        Returns:
            One result per child.
        """
        return self._write("PUT", [itemtype, items_id, sub_itemtype], items)

    def delete_sub_items(self, itemtype: str, items_id: int, sub_itemtype: str,
                         ids: Sequence[int]) -> list[OperationResult]:
        """Delete sub-items under one item.

        Args:
            itemtype: Parent itemtype.
            items_id: Parent id.
            sub_itemtype: Child itemtype.
            ids: Ids of the children.

        Returns:
            One result per child.
        """
        return self._write("DELETE", [itemtype, items_id, sub_itemtype], [{"id": child_id} for child_id in ids])

    # ------------------------------------------------------------- documents
    def upload_document(self, name: str, filepath: str | Path) -> int:
        """Upload a file as a new Document (multipart request).

        Args:
            name: Document name.
            filepath: Path of the file to upload.

        Returns:
            The id of the created Document.

        Raises:
            ConfigurationError: When the file does not exist.
        """
        path = Path(filepath)
        if not path.is_file():
            raise ConfigurationError(f"file not found: {path}")
        manifest = json.dumps({"input": {"name": name, "_filename": [path.name]}})
        with path.open("rb") as handle:
            # The JSON Content-Type of the session must not be sent with multipart bodies
            body = self._call("POST", ["Document"], ok=(201,), headers={"Content-Type": None},
                              data={"uploadManifest": manifest}, files={"filename[0]": (path.name, handle)})
        return int(body["id"])

    def download_document(self, documents_id: int, dirpath: str | Path, filename: str | None = None) -> Path:
        """Download the file of a Document.

        Args:
            documents_id: Document id.
            dirpath: Existing directory where the file is written.
            filename: File name; defaults to the name stored in GLPI.

        Returns:
            Path of the written file.

        Raises:
            ConfigurationError: When ``dirpath`` is not a directory.
        """
        directory = Path(dirpath)
        if not directory.is_dir():
            raise ConfigurationError(f"directory not found: {directory}")
        if filename is None:
            filename = str(self.get_item("Document", documents_id).get("filename") or f"document-{documents_id}")
        # Only the base name is used, so a stored name cannot escape the directory
        target = directory / Path(filename).name
        response = self._send("GET", ["Document", documents_id], headers={"Accept": "application/octet-stream"})
        if response.status_code != 200:
            raise self._error(response)
        target.write_bytes(response.content)
        return target


def _input_id(item: Any) -> int | None:
    """Return the ``id`` of an input item.

    Args:
        item: One element of the ``input`` payload.

    Returns:
        The id, or ``None``.
    """
    value = item.get("id") if isinstance(item, dict) else None
    return int(value) if isinstance(value, (int, str)) and str(value).isdigit() else None


def _parse_results(payload: Any) -> list[OperationResult]:
    """Normalize the per-item results of a write.

    Accepts ``{"id": 5, "message": ""}`` (add) and ``{"5": true, "message": ""}``
    (update and delete), as a list or a single object.

    Args:
        payload: Decoded body.

    Returns:
        One result per item.
    """
    rows = payload if isinstance(payload, list) else [payload]
    results = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        message = str(row.get("message") or "")
        if "id" in row:
            raw_id = row["id"]
            ok = bool(raw_id) and raw_id is not False
            results.append(OperationResult(id=int(raw_id) if ok else None, ok=ok, message=message))
            continue
        # {"<id>": bool, "message": ""}
        keys = [key for key in row if key != "message"]
        if keys:
            key = keys[0]
            results.append(OperationResult(id=int(key) if str(key).isdigit() else None, ok=bool(row[key]),
                                           message=message))
    return results


def _summary(results: list[OperationResult]) -> str:
    """Describe the failures of a bulk operation.

    Args:
        results: Per-item results.

    Returns:
        A short sentence with the failed count and messages.
    """
    failed = [result for result in results if not result.ok]
    messages = "; ".join(sorted({result.message for result in failed if result.message}))
    text = f"{len(failed)} of {len(results)} items failed"
    return f"{text}: {messages}" if messages else text


def _retry_after(value: str | None) -> float | None:
    """Parse a ``Retry-After`` header given in seconds.

    Args:
        value: Header value.

    Returns:
        Seconds to wait, or ``None`` when absent or not numeric (HTTP dates are ignored).
    """
    if value is None:
        return None
    try:
        return float(value)
    except ValueError:
        return None
