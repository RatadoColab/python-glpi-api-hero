"""Exception hierarchy of the library.

Every error raised by ``glpi_api_hero`` derives from :class:`GlpiError`::

    GlpiError
    ├── ConfigurationError          missing parameters, session not initialized
    ├── GlpiConnectionError         network, DNS, TLS, timeout (wraps requests exceptions)
    ├── GlpiAPIError                HTTP error answered by GLPI
    │   ├── BadRequestError         400
    │   ├── AuthenticationError     401 and login/token errors
    │   ├── PermissionDeniedError   403
    │   ├── NotFoundError           404
    │   ├── RateLimitError          429
    │   └── ServerError             5xx
    ├── PartialOperationError       bulk operation where some items failed
    └── UnsupportedOperationError   operation not available on the connected API
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from glpi_api_hero.core.types import OperationResult


class GlpiError(Exception):
    """Base class of every exception raised by the library."""


class ConfigurationError(GlpiError):
    """Invalid or missing configuration, or no open session."""


class GlpiConnectionError(GlpiError):
    """The GLPI server could not be reached (network, DNS, TLS or timeout)."""


class UnsupportedOperationError(GlpiError):
    """The operation is not available on the connected API version."""


class GlpiAPIError(GlpiError):
    """GLPI answered with an HTTP error.

    Attributes:
        status_code: HTTP status code.
        error_code: GLPI error key (``ERROR_*``), or ``None`` when absent.
        message: Human readable message sent by GLPI.
        response: The underlying HTTP response, when available.
    """

    def __init__(self, message: str, *, status_code: int | None = None, error_code: str | None = None,
                 response: Any = None) -> None:
        """Build the error.

        Args:
            message: Human readable message.
            status_code: HTTP status code.
            error_code: GLPI error key (``ERROR_*``).
            response: The underlying HTTP response.
        """
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.response = response

    def __str__(self) -> str:
        """Render ``(ERROR_CODE) message`` when the GLPI error key is known.

        Returns:
            The formatted message.
        """
        if self.error_code:
            return f"({self.error_code}) {self.message}"
        return self.message


class BadRequestError(GlpiAPIError):
    """The request was rejected as invalid (HTTP 400)."""


class AuthenticationError(GlpiAPIError):
    """Login, token or session error (HTTP 401 and authentication error keys)."""


class PermissionDeniedError(GlpiAPIError):
    """The active profile lacks the required right (HTTP 403)."""


class NotFoundError(GlpiAPIError):
    """The item or itemtype does not exist (HTTP 404)."""


class RateLimitError(GlpiAPIError):
    """Too many requests (HTTP 429).

    Attributes:
        retry_after: Seconds to wait before retrying, from the ``Retry-After`` header.
    """

    def __init__(self, message: str, *, retry_after: float | None = None, **kwargs: Any) -> None:
        """Build the error.

        Args:
            message: Human readable message.
            retry_after: Seconds to wait before retrying.
            **kwargs: Arguments of :class:`GlpiAPIError`.
        """
        super().__init__(message, **kwargs)
        self.retry_after = retry_after


class ServerError(GlpiAPIError):
    """GLPI failed while processing the request (HTTP 5xx)."""


class PartialOperationError(GlpiError):
    """A bulk add, update or delete succeeded only for some items.

    Attributes:
        results: One :class:`~glpi_api_hero.core.types.OperationResult` per input item.
        error_code: GLPI error key (``ERROR_GLPI_PARTIAL_*`` or ``ERROR_GLPI_DELETE``).
    """

    def __init__(self, message: str, results: list[OperationResult], *, error_code: str | None = None) -> None:
        """Build the error.

        Args:
            message: Human readable message.
            results: Per-item results.
            error_code: GLPI error key.
        """
        super().__init__(message)
        self.results = results
        self.error_code = error_code

    def __reduce__(self) -> tuple[Any, ...]:
        """Support pickling (``Exception`` rebuilds from ``args`` only).

        Returns:
            Reconstruction recipe.
        """
        return (_rebuild_partial, (str(self), self.results, self.error_code))

    @property
    def failed(self) -> list[OperationResult]:
        """Results of the items that failed.

        Returns:
            The failed results.
        """
        return [result for result in self.results if not result.ok]


def _rebuild_partial(message: str, results: list[OperationResult], error_code: str | None) -> PartialOperationError:
    """Rebuild a :class:`PartialOperationError` (used by pickle).

    Args:
        message: Message.
        results: Per-item results.
        error_code: GLPI error key.

    Returns:
        The exception.
    """
    return PartialOperationError(message, results, error_code=error_code)


# GLPI 10 error keys (src/Api/API.php, src/Api/APIRest.php) mapped to exception classes
ERROR_CODE_CLASSES: dict[str, type[GlpiAPIError]] = {
    # Authentication and session
    "ERROR_SESSION_TOKEN_INVALID": AuthenticationError,
    "ERROR_SESSION_TOKEN_MISSING": AuthenticationError,
    "ERROR_GLPI_LOGIN": AuthenticationError,
    "ERROR_GLPI_LOGIN_USER_TOKEN": AuthenticationError,
    "ERROR_LOGIN_PARAMETERS_MISSING": AuthenticationError,
    "ERROR_LOGIN_WITH_CREDENTIALS_DISABLED": AuthenticationError,
    "ERROR_LOGIN_WITH_TOKEN_DISABLED": AuthenticationError,
    "ERROR_APP_TOKEN_PARAMETERS_MISSING": AuthenticationError,
    "ERROR_WRONG_APP_TOKEN_PARAMETER": AuthenticationError,
    # Rights
    "ERROR_RIGHT_MISSING": PermissionDeniedError,
    "ERROR_NOT_ALLOWED_IP": PermissionDeniedError,
    # Missing items or itemtypes
    "ERROR_ITEM_NOT_FOUND": NotFoundError,
    "ERROR_ITEMTYPE_NOT_FOUND_NOR_COMMONDBTM": NotFoundError,
    "ERROR_RESOURCE_NOT_FOUND_NOR_COMMONDBTM": NotFoundError,
    "ERROR_MASSIVEACTION_NOT_FOUND": NotFoundError,
    # Invalid requests
    "ERROR_BAD_ARRAY": BadRequestError,
    "ERROR_FIELD_NOT_FOUND": BadRequestError,
    "ERROR_GLPI_ADD": BadRequestError,
    "ERROR_GLPI_UPDATE": BadRequestError,
    "ERROR_GLPI_DELETE": BadRequestError,
    "ERROR_RANGE_EXCEED_TOTAL": BadRequestError,
    "ERROR_METHOD_NOT_ALLOWED": BadRequestError,
    "ERROR_RESOURCE_MISSING": BadRequestError,
    "ERROR_JSON_PAYLOAD_FORBIDDEN": BadRequestError,
    "ERROR_JSON_PAYLOAD_INVALID": BadRequestError,
    "ERROR_UPLOAD_FILE_TOO_BIG_POST_MAX_SIZE": BadRequestError,
    "ERROR_MASSIVEACTION_KEY": BadRequestError,
    "ERROR_MASSIVEACTION_NO_IDS": BadRequestError,
    # Server side failures
    "ERROR_SQL": ServerError,
    "ERROR_UNKNOWN": ServerError,
}

# HTTP status used when the GLPI error key is absent or unknown
STATUS_CLASSES: dict[int, type[GlpiAPIError]] = {
    400: BadRequestError,
    401: AuthenticationError,
    403: PermissionDeniedError,
    404: NotFoundError,
    429: RateLimitError,
}


def error_class_for(status_code: int, error_code: str | None) -> type[GlpiAPIError]:
    """Choose the exception class for an HTTP error.

    Args:
        status_code: HTTP status code.
        error_code: GLPI error key, when present.

    Returns:
        The exception class: by error key first, then by status code.
    """
    if status_code == 429:
        return RateLimitError
    if error_code and error_code in ERROR_CODE_CLASSES:
        return ERROR_CODE_CLASSES[error_code]
    if status_code >= 500:
        return ServerError
    return STATUS_CLASSES.get(status_code, GlpiAPIError)


__all__ = [
    "AuthenticationError",
    "BadRequestError",
    "ConfigurationError",
    "ERROR_CODE_CLASSES",
    "GlpiAPIError",
    "GlpiConnectionError",
    "GlpiError",
    "NotFoundError",
    "PartialOperationError",
    "PermissionDeniedError",
    "RateLimitError",
    "ServerError",
    "UnsupportedOperationError",
    "error_class_for",
]
