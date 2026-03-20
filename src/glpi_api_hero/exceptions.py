
class GlpiApiHeroError(Exception):
    """Error base for package GlpiApiHero."""

class ApiConnectionError(GlpiApiHeroError, ValueError):
    """Errors related to API Connection."""

class ApiOperationError(GlpiApiHeroError, ValueError):
    """Errors related to API Operations."""