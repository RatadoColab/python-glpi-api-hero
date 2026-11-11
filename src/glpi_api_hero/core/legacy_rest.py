"""Connector for the legacy GLPI REST API (``apirest.php``, GLPI 9.5 to 12)."""

from __future__ import annotations

import base64
import json
import logging
import os
import re
import unicodedata
import urllib.parse
import uuid
import warnings
from collections.abc import Iterable, Sequence
from email.message import Message
from email.utils import decode_rfc2231
from pathlib import Path, PureWindowsPath
from typing import Any
from urllib.parse import unquote, urlsplit

import requests

from glpi_api_hero.core.connector import Connector
from glpi_api_hero.core.types import OperationResult
from glpi_api_hero.exceptions import (
    BadRequestError,
    ConfigurationError,
    GlpiAPIError,
    GlpiConnectionError,
    PartialOperationError,
    RateLimitError,
    error_class_for,
)

logger = logging.getLogger("glpi_api_hero")

DEFAULT_TIMEOUT = 30.0

# Request headers that carry credentials
_SECRET_HEADERS = ("Authorization", "Session-Token", "App-Token")


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
        try:
            parsed = urlsplit(url)
            parsed.port  # noqa: B018 - validates the port
        except ValueError as exc:
            raise ConfigurationError("the GLPI API URL is not valid") from exc
        if parsed.scheme.lower() not in ("http", "https") or not parsed.hostname:
            raise ConfigurationError("the GLPI API URL must be an absolute http(s) URL")
        if parsed.username or parsed.password:
            # Credentials in the URL would reach logs and error messages
            raise ConfigurationError("the GLPI API URL must not contain credentials")
        if parsed.query or parsed.fragment:
            raise ConfigurationError("the GLPI API URL must not contain a query or a fragment")
        if parsed.scheme.lower() == "http":
            logger.warning("the GLPI API URL uses plain http: tokens and passwords travel unencrypted")
            warnings.warn("the GLPI API URL uses plain http: tokens and passwords travel unencrypted",
                          stacklevel=2)
        self.url = url.rstrip("/")
        self.timeout = timeout
        self._app_token = app_token
        self._user_token = user_token
        self._username = username
        self._password = password
        self._session_token: str | None = None
        self._verify = _validate_verify(verify)
        self._http = requests.Session()
        self._http.verify = self._verify

    # ------------------------------------------------------------- transport
    @property
    def verify(self) -> bool | str:
        """TLS verification setting of the HTTP session.

        Returns:
            ``True``, ``False`` or the CA bundle path.
        """
        return self._verify

    def _redact(self, text: str) -> str:
        """Remove every known secret from a text.

        Args:
            text: Text that may contain secrets.

        Returns:
            The text with secrets replaced by ``***``.
        """
        for secret in self._secrets():
            text = text.replace(secret, "***")
        return text

    def _secrets(self) -> list[str]:
        """List the secrets (and their printable variants) to keep out of messages.

        Returns:
            Secrets, the Basic credentials encoding, and the ``repr()`` escaped form of each
            value (what an ``InvalidHeader`` message shows for tokens with whitespace).
        """
        raw = [self._app_token, self._user_token, self._password, self._session_token]
        if self._username:
            raw.append(base64.b64encode(f"{self._username}:{self._password}".encode()).decode())
        forms: list[str] = []
        for secret in raw:
            if not secret:
                continue
            for form in (secret, secret.strip(), repr(secret)[1:-1]):
                if form and form not in forms:
                    forms.append(form)
        # Longest first, so a secret that contains another one is fully masked
        return sorted(forms, key=len, reverse=True)

    def _scrub_exception(self, exc: requests.exceptions.RequestException) -> None:
        """Mask credentials in a ``requests`` exception before it is chained.

        Args:
            exc: The exception raised by ``requests``.
        """
        exc.request = self._scrubbed(exc.request)
        if exc.response is not None:
            self._scrub_response(exc.response)
        # The raw message may show header values (e.g. InvalidHeader)
        exc.args = tuple(self._redact(arg) if isinstance(arg, str) else arg for arg in exc.args)

    def _scrub_response(self, response: requests.Response) -> None:
        """Mask the credentials of a response's request and of its redirect history.

        Args:
            response: HTTP response (modified in place).
        """
        response.request = self._scrubbed(response.request)
        for previous in response.history:
            previous.request = self._scrubbed(previous.request)

    @staticmethod
    def _scrubbed(request: Any) -> Any:
        """Return a copy of a sent request with its credential headers masked.

        Exceptions keep a reference to the response (and its request), which may be
        logged or serialized; they get the masked copy, never the original.

        Args:
            request: ``requests.PreparedRequest`` (or ``None``).

        Returns:
            The masked copy, or ``request`` itself when it has no headers.
        """
        if request is None or getattr(request, "headers", None) is None:
            return request
        masked = request.copy()
        for name in _SECRET_HEADERS:
            if name in masked.headers:
                masked.headers[name] = "***"
        return masked

    def _endpoint(self, *parts: Any) -> str:
        """Build the absolute URL of an endpoint.

        Args:
            *parts: Path segments.

        Returns:
            The URL, with every segment percent-encoded.

        Raises:
            BadRequestError: When a segment is empty or is a dot segment (``.``/``..``), which
                would change the endpoint the request reaches.
        """
        segments = []
        for part in parts:
            text = str(part)
            if text in ("", ".", ".."):
                raise BadRequestError(f"invalid path segment: {text!r}")
            # Slashes and other reserved characters inside a segment never reach another endpoint
            segments.append(urllib.parse.quote(text, safe=""))
        return "/".join([self.url, *segments])

    def _send(self, method: str, parts: Iterable[Any], *, params: Any = None, body: Any = None,
              headers: dict[str, Any] | None = None, files: Any = None, data: Any = None,
              stream: bool = False) -> requests.Response:
        """Send one HTTP request, wrapping network errors.

        Args:
            method: HTTP method.
            parts: Endpoint path segments.
            params: Query parameters.
            body: JSON body.
            headers: Per-request headers.
            files: Multipart files.
            data: Multipart form fields.
            stream: Do not read the body immediately.

        Returns:
            The HTTP response.

        Raises:
            GlpiConnectionError: On network, TLS or timeout errors.
        """
        url = self._endpoint(*parts)
        try:
            # verify is passed on every call: False and a bundle path are never replaced by the environment,
            # while True still honors REQUESTS_CA_BUNDLE/CURL_CA_BUNDLE (requests behavior)
            response = self._http.request(method, url, params=params, json=body, headers=headers, files=files,
                                          data=data, timeout=self.timeout, verify=self._verify, stream=stream,
                                          allow_redirects=False)
        except requests.exceptions.InvalidJSONError as exc:
            # The payload could not be encoded (for example NaN): a caller error, not a network failure
            raise ValueError(f"the request payload is not valid JSON: {exc}") from None
        except requests.exceptions.RequestException as exc:
            self._scrub_exception(exc)
            raise GlpiConnectionError(self._redact(f"communication error: {exc}")) from exc
        except (ValueError, UnicodeError) as exc:
            # A malformed redirect target or URL surfaces as a plain ValueError from requests
            raise GlpiConnectionError(self._redact(f"communication error: {exc}")) from exc
        if 300 <= response.status_code < 400:
            response.close()
            raise ConfigurationError(
                f"GLPI answered with a redirect (HTTP {response.status_code}); redirects are not followed so that "
                "tokens never reach another host: configure the final API URL (for example https instead of http)")
        logger.debug("%s %s -> %s", method, "/".join(str(p) for p in parts), response.status_code)
        if "Content-Range" in response.headers:
            logger.debug("Content-Range: %s", response.headers["Content-Range"])
        return response

    def _error(self, response: requests.Response,
               items: Sequence[Any] | None = None) -> GlpiAPIError | PartialOperationError:
        """Build the exception that matches an error response.

        Args:
            response: HTTP response with an error status.
            items: ``input`` payload of a write, to reconcile per-item results.

        Returns:
            The exception to raise.
        """
        self._scrub_response(response)
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
        if isinstance(detail, list) or response.status_code == 207:
            # Bulk write where items failed: per-item results instead of a message
            results = _reconcile(_parse_results(detail if isinstance(detail, list) else []), items)
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
            The decoded JSON body, or ``None`` when the body is empty.

        Raises:
            GlpiAPIError: On error statuses, or when the body is not JSON.
            PartialOperationError: On bulk writes where items failed.
        """
        response = self._send(method, parts, **kwargs)
        if response.status_code not in ok:
            raise self._error(response)
        if not response.content:
            return None
        return self._decode(response)

    def _decode(self, response: requests.Response) -> Any:
        """Decode a successful JSON body.

        Args:
            response: HTTP response.

        Returns:
            The decoded body.

        Raises:
            GlpiAPIError: When the body is not JSON (proxy page, PHP warning...).
        """
        try:
            return response.json()
        except ValueError as exc:
            self._scrub_response(response)
            message = self._redact(f"invalid JSON answer: {response.text[:200]}")
            raise GlpiAPIError(message, status_code=response.status_code, response=response) from exc

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
            PartialOperationError: When some items failed (207, or 400 with per-item results).
        """
        response = self._send(method, parts, params=params, body={"input": list(items)})
        # Additions return the created ids, so only updates and deletes are reconciled by id
        sent = items if method != "POST" else None
        if response.status_code not in (200, 201, 204):
            raise self._error(response, sent)
        if not response.content:
            # 204 without body: every item succeeded
            return [OperationResult(id=_input_id(item), ok=True) for item in items]
        results = _reconcile(_parse_results(self._decode(response)), sent)
        failed = [result for result in results if not result.ok]
        if failed:
            raise PartialOperationError(self._redact(_summary(results)), results)
        return results

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
        if not isinstance(body, dict) or not isinstance(body.get("session_token"), str):
            raise GlpiAPIError("unexpected initSession answer: no session_token", status_code=200)
        self._session_token = body["session_token"]
        # Headers sent by every later request
        # Raw text is requested: by default GLPI 10 answers with HTML entities (``&`` as ``&#38;``)
        session_headers = {"Content-Type": "application/json", "Session-Token": self._session_token,
                           "X-GLPI-Sanitized-Content": "false"}
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

    def _call_ranged(self, method: str, parts: Iterable[Any], **kwargs: Any) -> Any:
        """Run a paginated read; a ``range`` beyond the total yields an empty result.

        Args:
            method: HTTP method.
            parts: Endpoint path segments.
            **kwargs: Arguments of :meth:`_call`.

        Returns:
            The decoded body, or ``None`` when the range starts after the last row.
        """
        try:
            return self._call(method, parts, ok=(200, 206), **kwargs)
        except BadRequestError as exc:
            if exc.error_code == "ERROR_RANGE_EXCEED_TOTAL":
                return None
            raise

    def get_all_items(self, itemtype: str, **params: Any) -> list[dict[str, Any]]:
        """Return the items of an itemtype.

        Args:
            itemtype: GLPI itemtype.
            **params: Extra API parameters.

        Returns:
            The items (empty list when there is none).
        """
        body = self._call_ranged("GET", [itemtype], params=_convert_bools(_expand_search_text(params)))
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
        body = self._call_ranged("GET", [itemtype, items_id, sub_itemtype], params=_convert_bools(params))
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
            # Meta criteria address the fields of their own itemtype
            field_itemtype = criterion.get("itemtype", itemtype) if criterion.get("meta") else itemtype
            for name, value in criterion.items():
                if name == "criteria":
                    continue
                if name == "field":
                    value = self.field_id(field_itemtype, value)
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
        query.update(_convert_bools(params))
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
        body = self._call_ranged("GET", ["search", itemtype], params=query)
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
        _require_ids(items)
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
        _require_ids(items)
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
        if not isinstance(body, dict) or not str(body.get("id", "")).isdigit():
            raise GlpiAPIError("unexpected Document upload answer: no id", status_code=201)
        documents_id = int(body["id"])
        uploads = (body.get("upload_result") or {}).get("filename") or []
        errors = [str(upload["error"]) for upload in uploads if isinstance(upload, dict) and upload.get("error")]
        if errors:
            # GLPI created the Document without its file: purge it before reporting the failure
            try:
                self.delete_items("Document", [documents_id], force_purge=True)
            except (GlpiAPIError, GlpiConnectionError, PartialOperationError):
                # The upload error is the one to report
                logger.warning("could not purge Document %s left without its file", documents_id)
            raise BadRequestError(self._redact("; ".join(errors)), status_code=201,
                                  error_code="ERROR_GLPI_INVALID_DOCUMENT")
        return documents_id

    def download_document(self, documents_id: int, dirpath: str | Path, filename: str | None = None,
                          mode: int = 0o600, overwrite: bool = False) -> Path:
        """Download the file of a Document.

        Args:
            documents_id: Document id.
            dirpath: Existing directory where the file is written.
            filename: File name; defaults to the name stored in GLPI.
            mode: Permissions of the new file (owner-only by default; documents may be confidential).
            overwrite: Replace a file that already exists with the same name.

        Returns:
            Path of the written file.

        Raises:
            ConfigurationError: When ``dirpath`` is not a directory.
            ValueError: When the final path would not sit directly inside ``dirpath``.
            FileExistsError: When the file exists and ``overwrite`` is false.
        """
        directory = Path(dirpath)
        if not directory.is_dir():
            raise ConfigurationError(f"directory not found: {directory}")
        response = self._send("GET", ["Document", documents_id], headers={"Accept": "application/octet-stream"},
                              stream=True)
        temp_path: str | None = None
        try:
            if response.status_code != 200:
                raise self._error(response)
            name = filename or _disposition_filename(response.headers.get("Content-Disposition"))
            # Only a plain file name is used, so a stored name cannot escape the directory
            target = directory / _safe_filename(name, f"document-{documents_id}")
            # Last guard: the final path must sit directly inside the destination directory
            # Only the parent is resolved: the final component is never followed by replace()/link()
            if target.parent.resolve() != directory.resolve():
                raise ValueError(f"download target outside {directory}: {target.name!r}")
            if not overwrite and (target.exists() or target.is_symlink()):
                raise FileExistsError(f"file already exists: {target}")
            # The file is written aside and renamed at the end: a failed transfer never leaves a partial file
            temp_path = str(directory / f".glpi-download-{uuid.uuid4().hex}")
            # Created with ``mode`` (minus the umask); owner-only unless the caller asks for more
            handle_fd = os.open(temp_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, mode)
            with os.fdopen(handle_fd, "wb") as handle:
                for chunk in response.iter_content(chunk_size=65536):
                    handle.write(chunk)
            if overwrite:
                Path(temp_path).replace(target)
            else:
                # A hard link fails when the name appeared meanwhile: nothing is overwritten
                try:
                    os.link(temp_path, target)
                except FileExistsError:
                    raise
                except OSError:
                    # Filesystems without hard links: fall back to the exclusive creation of the final name
                    with open(temp_path, "rb") as source, os.fdopen(
                            os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, mode), "wb") as sink:
                        sink.write(source.read())
            if not overwrite:
                Path(temp_path).unlink(missing_ok=True)
            temp_path = None
        except requests.exceptions.RequestException as exc:
            self._scrub_exception(exc)
            raise GlpiConnectionError(self._redact(f"communication error: {exc}")) from exc
        finally:
            response.close()
            if temp_path is not None:
                Path(temp_path).unlink(missing_ok=True)
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


def _require_ids(items: Sequence[Any]) -> None:
    """Refuse an update whose items do not all carry an ``id``.

    GLPI silently skips such items and answers 200, which would look like a success.

    Args:
        items: ``input`` payload of an update.

    Raises:
        BadRequestError: When an item has no usable ``id``.
    """
    if any(_input_id(item) is None for item in items):
        raise BadRequestError("every item to update needs an 'id'")


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


def _reconcile(results: list[OperationResult], items: Sequence[Any] | None) -> list[OperationResult]:
    """Align per-item results with the ids sent (update and delete).

    GLPI omits the result of an item it could not find on update; every sent id
    without a result is reported as failed.

    Args:
        results: Parsed results.
        items: ``input`` payload (``None`` when unknown).

    Returns:
        One result per input item when the items carry ids, otherwise ``results``.
    """
    ids = [_input_id(item) for item in items or []]
    if not ids or any(items_id is None for items_id in ids):
        return results
    by_id = {result.id: result for result in results if result.id is not None}
    return [by_id.get(items_id, OperationResult(items_id, False, "Item not found")) for items_id in ids]


def _validate_verify(verify: Any) -> bool | str:
    """Check the TLS setting.

    Args:
        verify: ``True``, ``False`` or the path of a CA bundle (file or directory).

    Returns:
        The validated value.

    Raises:
        ConfigurationError: For other values or a missing CA bundle path.
    """
    if isinstance(verify, bool):
        return verify
    if isinstance(verify, (str, Path)) and str(verify) and Path(verify).exists():
        # Absolute, so a later chdir cannot change which bundle is used
        return str(Path(verify).resolve())
    raise ConfigurationError(f"verify_tls must be True, False or an existing CA bundle path, got {verify!r}")


def _disposition_filename(header: str | None) -> str | None:
    """Extract the file name of a ``Content-Disposition`` header.

    The RFC 5987 form (``filename*=utf-8''...``), which GLPI sends next to the
    Latin-1 ``filename=``, wins; otherwise the quoted form is decoded.

    Args:
        header: Header value.

    Returns:
        The file name, or ``None``.
    """
    if not header:
        return None
    extended = re.search(r"filename\*\s*=\s*([^;]+)", header)
    if extended:
        charset, _language, encoded = decode_rfc2231(extended.group(1).strip())
        try:
            return unquote(encoded, encoding=charset or "utf-8", errors="strict") or None
        except (LookupError, UnicodeDecodeError):
            pass
    message = Message()
    message["Content-Disposition"] = header
    name = message.get_filename()
    # The email parser unescapes ``\\`` and ``\"``; PHP addslashes also escapes the apostrophe
    return re.sub(r"\\'", "'", name) if name else None


def _safe_filename(name: str | None, default: str) -> str:
    """Reduce a server-provided name to a plain file name.

    Args:
        name: Name sent by the server (may contain directories or be ``.``/``..``).
        default: Name used when ``name`` leaves nothing usable.

    Returns:
        A name that cannot leave the destination directory.
    """
    # Both separators are cut, whatever the server platform
    base = (name or "").replace("\\", "/").rsplit("/", 1)[-1].strip()
    # Drive prefixes such as "C:" are dropped (they escape the directory on Windows)
    base = PureWindowsPath(base).name
    # Control characters (NUL, newlines, escapes, DEL) are removed
    base = "".join(char for char in base if unicodedata.category(char) not in ("Cc", "Cf", "Zl", "Zp")).strip()
    return default if base in ("", ".", "..") else base
