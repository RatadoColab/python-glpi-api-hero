"""Provisional sub-item and stub classes, replaced by the typed models of phases 05 to 08."""

from glpi_api_hero.core.common_dbtm import CommonDBTM


class Actor(CommonDBTM):
    """Ticket actor link (``Ticket_User``)."""

    _glpi_name = "Ticket_User"


class Item(CommonDBTM):
    """Item linked to a ticket (``Item_Ticket``)."""

    _glpi_name = "Item_Ticket"


class Task(CommonDBTM):
    """Ticket task (``TicketTask``)."""

    _glpi_name = "TicketTask"


class LinkedTicket(CommonDBTM):
    """Link between two tickets (``Ticket_Ticket``)."""

    _glpi_name = "Ticket_Ticket"


class ITILFollowup(CommonDBTM):
    """Follow-up of a ticket (placeholder)."""


class ITILSolution(CommonDBTM):
    """Solution of a ticket (placeholder)."""


class TicketValidation(CommonDBTM):
    """Validation request of a ticket (placeholder)."""


class Cluster(CommonDBTM):
    """Cluster (placeholder)."""


class NetworkEquipment(CommonDBTM):
    """Network equipment (placeholder)."""

    # Search option id of the location (GLPI 10 rawSearchOptions)
    SEARCH_FIELD_LOCATION = 3
