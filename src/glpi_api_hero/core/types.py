"""Value types shared by connectors and models."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class OperationResult:
    """Result of one item in an add, update or delete operation.

    Attributes:
        id: Id of the item (created id for additions), or ``None`` when unknown.
        ok: Whether the operation succeeded for this item.
        message: Message sent by GLPI (empty on success).
    """

    id: int | None
    ok: bool
    message: str = ""
