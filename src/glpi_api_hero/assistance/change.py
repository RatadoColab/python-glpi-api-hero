"""Changes (Assistance > Changes)."""

from __future__ import annotations

from typing import ClassVar

from glpi_api_hero.core.common_itil import CommonITILObject
from glpi_api_hero.core.constants import ActorKind


class Change(CommonITILObject):
    """GLPI changes, with their sub-items inherited from ``CommonITILObject``."""

    _task_itemtype: ClassVar[str] = "ChangeTask"
    _validation_itemtype: ClassVar[str | None] = "ChangeValidation"
    _actor_itemtypes: ClassVar[dict[ActorKind, str]] = {
        ActorKind.USER: "Change_User",
        ActorKind.GROUP: "Change_Group",
        ActorKind.SUPPLIER: "Change_Supplier",
    }
    _item_link_itemtype: ClassVar[str] = "Change_Item"
    _cost_itemtype: ClassVar[str] = "ChangeCost"
    _foreign_key: ClassVar[str] = "changes_id"
    _links: ClassVar[dict[str, tuple[str, str, str]]] = {
        "tickets": ("Change_Ticket", "changes_id", "tickets_id"),
        "problems": ("Change_Problem", "changes_id", "problems_id"),
    }
