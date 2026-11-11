"""Models of the Assets menu."""

from glpi_api_hero.assets.cable import Cable
from glpi_api_hero.assets.cartridge_item import CartridgeItem
from glpi_api_hero.assets.computer import Computer
from glpi_api_hero.assets.consumable_item import ConsumableItem
from glpi_api_hero.assets.enclosure import Enclosure
from glpi_api_hero.assets.monitor import Monitor
from glpi_api_hero.assets.network_equipment import NetworkEquipment
from glpi_api_hero.assets.passive_dc_equipment import PassiveDCEquipment
from glpi_api_hero.assets.pdu import PDU
from glpi_api_hero.assets.peripheral import Peripheral
from glpi_api_hero.assets.phone import Phone
from glpi_api_hero.assets.printer import Printer
from glpi_api_hero.assets.rack import Rack
from glpi_api_hero.assets.software import Software
from glpi_api_hero.assets.unmanaged import Unmanaged

__all__ = [
    "Cable",
    "CartridgeItem",
    "Computer",
    "ConsumableItem",
    "Enclosure",
    "Monitor",
    "NetworkEquipment",
    "PDU",
    "PassiveDCEquipment",
    "Peripheral",
    "Phone",
    "Printer",
    "Rack",
    "Software",
    "Unmanaged",
]
