"""Racks (GLPI ``Rack``)."""

from __future__ import annotations

from typing import Any

from glpi_api_hero.core.capabilities import HasContracts, HasDocuments, HasInfocom, HasTickets
from glpi_api_hero.core.common_asset import CommonAsset


class Rack(CommonAsset, HasInfocom, HasContracts, HasDocuments, HasTickets):
    """GLPI ``Rack`` (Assets > Racks)."""

    @classmethod
    def get_items(cls, rack_id: int, **params: Any) -> list[dict[str, Any]]:
        """Return the equipment mounted in the rack (``Item_Rack``).

        Args:
            rack_id: Rack id.
            **params: Extra API parameters.

        Returns:
            The rows.
        """
        return cls.get_sub_items(rack_id, "Item_Rack", **params)

    @classmethod
    def get_pdus(cls, rack_id: int, **params: Any) -> list[dict[str, Any]]:
        """Return the PDUs of the rack (``PDU_Rack``).

        Args:
            rack_id: Rack id.
            **params: Extra API parameters.

        Returns:
            The rows.
        """
        return cls.get_sub_items(rack_id, "PDU_Rack", **params)
