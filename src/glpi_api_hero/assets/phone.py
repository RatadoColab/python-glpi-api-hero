"""Phones (GLPI ``Phone``)."""

from __future__ import annotations

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
    HasRemoteManagement,
    HasReservation,
    HasSimCards,
    HasSoftware,
    HasTickets,
)
from glpi_api_hero.core.common_asset import CommonAsset


class Phone(
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
    HasRemoteManagement,
    HasReservation,
    HasTickets,
):
    """GLPI ``Phone`` (Assets > Phones)."""
