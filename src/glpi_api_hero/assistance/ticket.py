"""Tickets (Assistance > Tickets)."""

from __future__ import annotations

from typing import Any, ClassVar

from glpi_api_hero.core.common_itil import CommonITILObject
from glpi_api_hero.core.constants import ActorKind
from glpi_api_hero.exceptions import NotFoundError


class Ticket(CommonITILObject):
    """GLPI tickets, with their sub-items inherited from ``CommonITILObject``."""

    # Search option ids of the Ticket itemtype (GLPI 10 rawSearchOptions)
    SEARCH_FIELD_ITEM_TYPE = 131
    SEARCH_FIELD_ITEM_ID = 13
    SEARCH_FIELD_LOCATION = 83

    _task_itemtype: ClassVar[str] = "TicketTask"
    _validation_itemtype: ClassVar[str | None] = "TicketValidation"
    _actor_itemtypes: ClassVar[dict[ActorKind, str]] = {
        ActorKind.USER: "Ticket_User",
        ActorKind.GROUP: "Group_Ticket",
        ActorKind.SUPPLIER: "Supplier_Ticket",
    }
    _item_link_itemtype: ClassVar[str] = "Item_Ticket"
    _cost_itemtype: ClassVar[str] = "TicketCost"
    _foreign_key: ClassVar[str] = "tickets_id"
    _links: ClassVar[dict[str, tuple[str, str, str]]] = {
        "tickets": ("Ticket_Ticket", "tickets_id_1", "tickets_id_2"),
        "problems": ("Problem_Ticket", "tickets_id", "problems_id"),
        "changes": ("Change_Ticket", "tickets_id", "changes_id"),
    }

    @classmethod
    def get_satisfaction(cls, itil_id: int) -> dict[str, Any]:
        """Return the satisfaction survey of a ticket.

        Args:
            itil_id: Ticket id.

        Returns:
            The survey fields.

        Raises:
            NotFoundError: When the ticket has no survey.
        """
        rows = cls.get_sub_items(itil_id, "TicketSatisfaction")
        if not rows:
            raise NotFoundError(f"ticket {itil_id} has no satisfaction survey")
        return rows[0]
