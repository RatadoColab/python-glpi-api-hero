"""PDUs (GLPI ``PDU``)."""

from __future__ import annotations

from glpi_api_hero.core.capabilities import HasContracts, HasInfocom, HasNetworkPorts, HasRack, HasTickets
from glpi_api_hero.core.common_asset import CommonAsset


class PDU(CommonAsset, HasInfocom, HasNetworkPorts, HasContracts, HasRack, HasTickets):
    """GLPI ``PDU`` (Assets > PDUs)."""
