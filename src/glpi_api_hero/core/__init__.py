"""Library core: connector contract, legacy REST connector, session facade and generic CRUD."""

from glpi_api_hero.core.common_dbtm import CommonDBTM
from glpi_api_hero.core.common_itil import CommonITILObject
from glpi_api_hero.core.connector import Connector
from glpi_api_hero.core.constants import ActorKind, ActorType, LinkType
from glpi_api_hero.core.generic_item import GenericItem
from glpi_api_hero.core.legacy_rest import LegacyRestConnector
from glpi_api_hero.core.session import Glpi
from glpi_api_hero.core.types import OperationResult

__all__ = [
    "ActorKind",
    "ActorType",
    "CommonDBTM",
    "CommonITILObject",
    "Connector",
    "GenericItem",
    "Glpi",
    "LegacyRestConnector",
    "LinkType",
    "OperationResult",
]
