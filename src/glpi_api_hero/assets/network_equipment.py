"""Networking devices (GLPI ``NetworkEquipment``)."""

from __future__ import annotations

from glpi_api_hero.core.capabilities import (
    HasAppliances,
    HasCertificates,
    HasClusters,
    HasContracts,
    HasDevices,
    HasDisks,
    HasDocuments,
    HasDomains,
    HasInfocom,
    HasNetworkPorts,
    HasNotes,
    HasOperatingSystem,
    HasRack,
    HasReservation,
    HasSimCards,
    HasSoftware,
    HasTickets,
)
from glpi_api_hero.core.common_asset import CommonAsset


class NetworkEquipment(
    CommonAsset,
    HasNotes,
    HasInfocom,
    HasNetworkPorts,
    HasContracts,
    HasDocuments,
    HasCertificates,
    HasDomains,
    HasAppliances,
    HasClusters,
    HasSoftware,
    HasOperatingSystem,
    HasDisks,
    HasDevices,
    HasSimCards,
    HasRack,
    HasReservation,
    HasTickets,
):
    """GLPI ``NetworkEquipment`` (Assets > Networking devices)."""
