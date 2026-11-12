"""Cartridge models (GLPI ``CartridgeItem``)."""

from __future__ import annotations

from typing import Any

from glpi_api_hero.core.capabilities import HasDocuments, HasInfocom, HasLogs, HasNotes


class CartridgeItem(HasInfocom, HasDocuments, HasNotes, HasLogs):
    """GLPI ``CartridgeItem`` (Assets > Cartridge models)."""

    @classmethod
    def get_cartridges(cls, cartridgeitem_id: int, **params: Any) -> list[dict[str, Any]]:
        """Return the cartridges of the model (``Cartridge``).

        Args:
            cartridgeitem_id: Cartridge model id.
            **params: Extra API parameters.

        Returns:
            The rows.
        """
        return cls.get_sub_items(cartridgeitem_id, "Cartridge", **params)

    @classmethod
    def get_compatible_printer_models(cls, cartridgeitem_id: int, **params: Any) -> list[dict[str, Any]]:
        """Return the printer models the cartridge fits (``CartridgeItem_PrinterModel``).

        Args:
            cartridgeitem_id: Cartridge model id.
            **params: Extra API parameters.

        Returns:
            The rows.
        """
        return cls.get_sub_items(cartridgeitem_id, "CartridgeItem_PrinterModel", **params)
