"""Problems (Assistance > Problems)."""

from __future__ import annotations

from typing import ClassVar

from glpi_api_hero.core.common_itil import CommonITILObject
from glpi_api_hero.core.constants import ActorKind


class Problem(CommonITILObject):
    """GLPI problems, with their sub-items inherited from ``CommonITILObject``.

    Problems have no validations: the validation methods raise ``UnsupportedOperationError``.
    """

    _task_itemtype: ClassVar[str] = "ProblemTask"
    _validation_itemtype: ClassVar[str | None] = None
    _actor_itemtypes: ClassVar[dict[ActorKind, str]] = {
        ActorKind.USER: "Problem_User",
        ActorKind.GROUP: "Group_Problem",
        ActorKind.SUPPLIER: "Problem_Supplier",
    }
    _item_link_itemtype: ClassVar[str] = "Item_Problem"
    _cost_itemtype: ClassVar[str] = "ProblemCost"
    _foreign_key: ClassVar[str] = "problems_id"
    _links: ClassVar[dict[str, tuple[str, str, str]]] = {
        "tickets": ("Problem_Ticket", "problems_id", "tickets_id"),
        "changes": ("Change_Problem", "problems_id", "changes_id"),
    }
