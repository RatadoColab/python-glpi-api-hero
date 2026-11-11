"""Devices (GLPI ``Peripheral``)."""

from __future__ import annotations

from glpi_api_hero.core.capabilities import (
    HasAppliances,
    HasCertificates,
    HasContracts,
    HasDevices,
    HasDocuments,
    HasDomains,
    HasInfocom,
    HasNetworkPorts,
    HasOperatingSystem,
    HasRack,
    HasReservation,
    HasSimCards,
    HasSoftware,
    HasTickets,
)
from glpi_api_hero.core.common_asset import CommonAsset


class Peripheral(
    CommonAsset,
    HasInfocom,
    HasNetworkPorts,
    HasContracts,
    HasDocuments,
    HasCertificates,
    HasDomains,
    HasAppliances,
    HasSoftware,
    HasOperatingSystem,
    HasDevices,
    HasSimCards,
    HasRack,
    HasReservation,
    HasTickets,
):
    """GLPI ``Peripheral`` (Assets > Devices)."""
