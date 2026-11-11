"""Printers (GLPI ``Printer``)."""

from __future__ import annotations

from typing import Any

from glpi_api_hero.core.capabilities import (
    HasAppliances,
    HasCertificates,
    HasContracts,
    HasDevices,
    HasDisks,
    HasDocuments,
    HasDomains,
    HasInfocom,
    HasNetworkPorts,
    HasNotes,
    HasOperatingSystem,
    HasReservation,
    HasSimCards,
    HasSoftware,
    HasTickets,
)
from glpi_api_hero.core.common_asset import CommonAsset


class Printer(
    CommonAsset,
    HasNotes,
    HasInfocom,
    HasNetworkPorts,
    HasContracts,
    HasDocuments,
    HasCertificates,
    HasDomains,
    HasAppliances,
    HasSoftware,
    HasOperatingSystem,
    HasDisks,
    HasDevices,
    HasSimCards,
    HasReservation,
    HasTickets,
):
    """GLPI ``Printer`` (Assets > Printers)."""

    @classmethod
    def get_cartridges(cls, printer_id: int, **params: Any) -> list[dict[str, Any]]:
        """Return the cartridges installed in the printer (``Cartridge``).

        Args:
            printer_id: Printer id.
            **params: Extra API parameters.

        Returns:
            The rows.
        """
        return cls.get_sub_items(printer_id, "Cartridge", **params)
