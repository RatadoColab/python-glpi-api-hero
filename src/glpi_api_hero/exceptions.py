
class GlpiApiHeroError(Exception):
    """Error base for package GlpiApiHero."""

class ApiConnectionError(GlpiApiHeroError, ValueError):
    """Errors related to API Connection."""

class ApiOperationError(GlpiApiHeroError, ValueError):
    """Errors related to API Operations."""

class ApiRateLimitError(ApiOperationError):
    """Raised when the GLPI API returns HTTP 429 Too Many Requests."""