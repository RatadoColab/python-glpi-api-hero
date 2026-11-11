"""Unmanaged devices (GLPI ``Unmanaged``)."""

from __future__ import annotations

from glpi_api_hero.core.capabilities import HasDomains, HasNetworkPorts
from glpi_api_hero.core.common_asset import CommonAsset


class Unmanaged(CommonAsset, HasNetworkPorts, HasDomains):
    """GLPI ``Unmanaged`` (Assets > Unmanaged devices)."""

    # Search option ids of the Unmanaged itemtype (GLPI 10 rawSearchOptions)
    SEARCH_FIELD_SERIAL = 4
    SEARCH_FIELD_INVENTORY_NUMBER = 5
