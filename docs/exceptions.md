# Exceptions

All library errors derive from `GlpiError` (`glpi_api_hero.exceptions`).

| Exception | When |
|---|---|
| `ConfigurationError` | Missing or invalid configuration, no open session |
| `GlpiConnectionError` | The server could not be reached (network, TLS, timeout) |
| `GlpiAPIError` | GLPI answered with an HTTP error (`status_code`, `error_code`, `message`) |
| `AuthenticationError` | Invalid tokens or credentials |
| `PermissionDeniedError` | The active profile cannot read the item or the operation (a refused write may surface as `BadRequestError` with `ERROR_GLPI_ADD`, `ERROR_GLPI_UPDATE` or `ERROR_GLPI_DELETE`) |
| `NotFoundError` | The item does not exist |
| `BadRequestError` | GLPI refused the data |
| `RateLimitError` | The server asked the client to slow down (HTTP 429) |
| `ServerError` | GLPI failed (HTTP 5xx) |
| `PartialOperationError` | A bulk write succeeded only for some items (`results`, `failed`) |
| `UnsupportedOperationError` | The operation does not exist for the item or the connector |

`ValueError` is raised for invalid arguments before any request is sent.

```python
from glpi_api_hero import NotFoundError, RateLimitError
from glpi_api_hero.assets import Computer

try:
    Computer.get(999)
except NotFoundError:
    print("no such computer")
except RateLimitError:
    ...  # wait and retry
```

Searches without results return an empty list; only a missing single item raises `NotFoundError`.
