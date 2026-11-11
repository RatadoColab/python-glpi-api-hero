"""Python client for the GLPI REST API."""

import logging

from glpi_api_hero.__version__ import __version__
from glpi_api_hero.core.common_dbtm import CommonDBTM
from glpi_api_hero.core.generic_item import GenericItem
from glpi_api_hero.core.session import Glpi
from glpi_api_hero.exceptions import (
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
)

# Library logger: silent unless the application configures logging
logging.getLogger("glpi_api_hero").addHandler(logging.NullHandler())

__all__ = [
    "__version__",
    "AuthenticationError",
    "BadRequestError",
    "CommonDBTM",
    "ConfigurationError",
    "GenericItem",
    "GlpiAPIError",
    "GlpiConnectionError",
    "GlpiError",
    "Glpi",
    "NotFoundError",
    "PartialOperationError",
    "PermissionDeniedError",
    "RateLimitError",
    "ServerError",
    "UnsupportedOperationError",
]
