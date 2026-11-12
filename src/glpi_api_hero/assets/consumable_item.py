"""Consumable models (GLPI ``ConsumableItem``)."""

from __future__ import annotations

from typing import Any

from glpi_api_hero.core.capabilities import HasDocuments, HasInfocom, HasLogs, HasNotes


class ConsumableItem(HasInfocom, HasDocuments, HasNotes, HasLogs):
    """GLPI ``ConsumableItem`` (Assets > Consumable models)."""

    @classmethod
    def get_consumables(cls, consumableitem_id: int, **params: Any) -> list[dict[str, Any]]:
        """Return the consumables of the model (``Consumable``).

        Args:
            consumableitem_id: Consumable model id.
            **params: Extra API parameters.

        Returns:
            The rows.
        """
        return cls.get_sub_items(consumableitem_id, "Consumable", **params)
