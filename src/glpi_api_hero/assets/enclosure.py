"""Enclosures (GLPI ``Enclosure``)."""

from __future__ import annotations

from typing import Any

from glpi_api_hero.core.capabilities import HasContracts, HasDevices, HasInfocom, HasNetworkPorts, HasRack, HasTickets
from glpi_api_hero.core.common_asset import CommonAsset


class Enclosure(CommonAsset, HasInfocom, HasNetworkPorts, HasContracts, HasDevices, HasRack, HasTickets):
    """GLPI ``Enclosure`` (Assets > Enclosures)."""

    @classmethod
    def get_items(cls, enclosure_id: int, **params: Any) -> list[dict[str, Any]]:
        """Return the equipment installed in the enclosure (``Item_Enclosure``).

        Args:
            enclosure_id: Enclosure id.
            **params: Extra API parameters.

        Returns:
            The rows.
        """
        return cls.get_sub_items(enclosure_id, "Item_Enclosure", **params)
