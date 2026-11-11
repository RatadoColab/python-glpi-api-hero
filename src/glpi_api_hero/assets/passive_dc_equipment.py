"""Passive devices (GLPI ``PassiveDCEquipment``)."""

from __future__ import annotations

from glpi_api_hero.core.capabilities import HasContracts, HasInfocom, HasRack, HasTickets
from glpi_api_hero.core.common_asset import CommonAsset


class PassiveDCEquipment(CommonAsset, HasInfocom, HasContracts, HasRack, HasTickets):
    """GLPI ``PassiveDCEquipment`` (Assets > Passive devices)."""
