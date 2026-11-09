"""Python client for the GLPI REST API."""

import logging

from glpi_api_hero.__version__ import __version__
from glpi_api_hero.actor import Actor
from glpi_api_hero.api_communication import ApiCommunication
from glpi_api_hero.cluster import Cluster
from glpi_api_hero.computer import Computer
from glpi_api_hero.core import CommonDBTM, Connector, Glpi, LegacyRestConnector, OperationResult
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
from glpi_api_hero.group import Group
from glpi_api_hero.item import Item
from glpi_api_hero.itilfollowup import ITILFollowup
from glpi_api_hero.itilsolution import ITILSolution
from glpi_api_hero.linked_ticket import LinkedTicket
from glpi_api_hero.location import Location
from glpi_api_hero.network_equipment import NetworkEquipment
from glpi_api_hero.task import Task
from glpi_api_hero.ticket import Ticket
from glpi_api_hero.ticket_dashboard import TicketDashboard
from glpi_api_hero.ticket_validation import TicketValidation
from glpi_api_hero.user import User

# Library logger: silent unless the application configures logging
logging.getLogger("glpi_api_hero").addHandler(logging.NullHandler())

__all__ = [
    "__version__",
    "AuthenticationError",
    "BadRequestError",
    "ConfigurationError",
    "GlpiAPIError",
    "GlpiConnectionError",
    "GlpiError",
    "NotFoundError",
    "PartialOperationError",
    "PermissionDeniedError",
    "RateLimitError",
    "ServerError",
    "UnsupportedOperationError",
    "CommonDBTM",
    "Connector",
    "Glpi",
    "LegacyRestConnector",
    "OperationResult",
    "ApiCommunication",
    "Actor",
    "Item",
    "User",
    "Group",
    "Computer",
    "Cluster",
    "NetworkEquipment",
    "ITILFollowup",
    "ITILSolution",
    "TicketValidation",
    "Task",
    "LinkedTicket",
    "Location",
    "Ticket",
    "TicketDashboard",
]
