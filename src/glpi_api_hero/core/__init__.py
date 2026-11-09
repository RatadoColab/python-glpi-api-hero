"""Library core: connector contract, legacy REST connector, session facade and generic CRUD."""

from glpi_api_hero.core.common_dbtm import CommonDBTM
from glpi_api_hero.core.connector import Connector
from glpi_api_hero.core.legacy_rest import LegacyRestConnector
from glpi_api_hero.core.session import Glpi
from glpi_api_hero.core.types import OperationResult

__all__ = ["CommonDBTM", "Connector", "Glpi", "LegacyRestConnector", "OperationResult"]
