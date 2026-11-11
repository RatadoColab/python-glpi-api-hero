"""Monitors (GLPI ``Monitor``)."""

from __future__ import annotations

from glpi_api_hero.core.capabilities import (
    HasAppliances,
    HasContracts,
    HasDocuments,
    HasDomains,
    HasInfocom,
    HasNetworkPorts,
    HasOperatingSystem,
    HasRack,
    HasReservation,
    HasSoftware,
    HasTickets,
)
from glpi_api_hero.core.common_asset import CommonAsset


class Monitor(
    CommonAsset,
    HasInfocom,
    HasNetworkPorts,
    HasContracts,
    HasDocuments,
    HasDomains,
    HasAppliances,
    HasSoftware,
    HasOperatingSystem,
    HasRack,
    HasReservation,
    HasTickets,
):
    """GLPI ``Monitor`` (Assets > Monitors)."""
