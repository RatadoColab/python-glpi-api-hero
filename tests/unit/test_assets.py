"""Asset models: the base lookups and the specific methods send the requests GLPI 10 expects."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest

from glpi_api_hero import assets
from glpi_api_hero.components import DeviceSimcard
from tests.conftest import GlpiMock

# (id, call, expected path of the single request)
SUB_ITEM_CALLS: list[tuple[str, Callable[[], Any], str]] = [
    ("computer-virtual-machines", lambda: assets.Computer.get_virtual_machines(1), "Computer/1/ComputerVirtualMachine"),
    ("computer-connections", lambda: assets.Computer.get_connections(1), "Computer/1/Computer_Item"),
    ("printer-cartridges", lambda: assets.Printer.get_cartridges(2), "Printer/2/Cartridge"),
    ("cartridgeitem-cartridges", lambda: assets.CartridgeItem.get_cartridges(3), "CartridgeItem/3/Cartridge"),
    ("cartridgeitem-printer-models", lambda: assets.CartridgeItem.get_compatible_printer_models(3),
     "CartridgeItem/3/CartridgeItem_PrinterModel"),
    ("consumableitem-consumables", lambda: assets.ConsumableItem.get_consumables(4), "ConsumableItem/4/Consumable"),
    ("rack-items", lambda: assets.Rack.get_items(5), "Rack/5/Item_Rack"),
    ("rack-pdus", lambda: assets.Rack.get_pdus(5), "Rack/5/PDU_Rack"),
    ("enclosure-items", lambda: assets.Enclosure.get_items(6), "Enclosure/6/Item_Enclosure"),
    ("software-versions", lambda: assets.Software.get_versions(7), "Software/7/SoftwareVersion"),
    ("software-licenses", lambda: assets.Software.get_licenses(7), "Software/7/SoftwareLicense"),
    ("simcard-installations", lambda: DeviceSimcard.get_installations(8), "DeviceSimcard/8/Item_DeviceSimcard"),
    ("monitor-infocom", lambda: assets.Monitor.get_infocom(9), "Monitor/9/Infocom"),
    ("phone-remote-management", lambda: assets.Phone.get_remote_managements(9), "Phone/9/Item_RemoteManagement"),
    ("computer-sim-cards", lambda: assets.Computer.get_sim_cards(9), "Computer/9/Item_DeviceSimcard"),
    ("peripheral-racks", lambda: assets.Peripheral.get_racks(9), "Peripheral/9/Item_Rack"),
    ("printer-tickets", lambda: assets.Printer.get_tickets(9), "Printer/9/Item_Ticket"),
    ("monitor-notes", lambda: assets.Monitor.get_notes(9), "Monitor/9/Notepad"),
    ("cable-logs", lambda: assets.Cable.get_logs(9), "Cable/9/Log"),
    ("monitor-reservation", lambda: assets.Monitor.get_reservation_items(9), "Monitor/9/ReservationItem"),
    ("networkequipment-clusters", lambda: assets.NetworkEquipment.get_clusters(9), "NetworkEquipment/9/Item_Cluster"),
    ("computer-licenses", lambda: assets.Computer.get_software_licenses(9), "Computer/9/Item_SoftwareLicense"),
]


@pytest.mark.parametrize(("call", "path"), [(c, p) for _, c, p in SUB_ITEM_CALLS],
                         ids=[i for i, _, _ in SUB_ITEM_CALLS])
def test_sub_item_methods(session: GlpiMock, call: Callable[[], Any], path: str) -> None:
    """Each reader is one GET on ``<Itemtype>/<id>/<Sub-itemtype>``."""
    call()
    requests = session.captured()
    assert [(r["method"], r["path"]) for r in requests] == [("GET", path)]


ASSET_CLASSES = ["Computer", "Monitor", "NetworkEquipment", "Peripheral", "Printer", "Phone", "Rack", "Enclosure",
                 "PDU", "PassiveDCEquipment"]


@pytest.mark.parametrize("name", ASSET_CLASSES)
def test_common_asset_searches(session: GlpiMock, name: str) -> None:
    """Name, serial and inventory number use the search options 1, 5 and 6 of GLPI 10."""
    model = getattr(assets, name)
    for method, value, field, searchtype in (("get_by_name", "srv", "1", "contains"),
                                             ("get_by_serial", "S1", "5", "equals"),
                                             ("get_by_inventory_number", "P1", "6", "equals")):
        session.reset_calls()
        getattr(model, method)(value, range="0-4")
        query = session.captured()[0]["query"]
        assert session.captured()[0]["path"] == f"search/{name}"
        assert (query["criteria[0][field]"], query["criteria[0][searchtype]"], query["criteria[0][value]"]) == (
            field, searchtype, value)
        assert query["range"] == "0-4"


def test_unmanaged_uses_its_own_serial_fields(session: GlpiMock) -> None:
    """``Unmanaged`` numbers its serial and inventory options 4 and 5 (``src/Unmanaged.php``)."""
    assets.Unmanaged.get_by_serial("S")
    assets.Unmanaged.get_by_inventory_number("P")
    fields = [call["query"]["criteria[0][field]"] for call in session.captured()]
    assert fields == ["4", "5"]


def test_get_installations_reads_each_version(session: GlpiMock) -> None:
    """GLPI does not filter ``Item_SoftwareVersion`` by software: one request per version of the software."""
    session.override("GET", "Software/7/SoftwareVersion", 200, [{"id": 31}, {"id": 32}])
    assets.Software.get_installations(7, range="0-9")
    assert [c["path"] for c in session.captured()] == [
        "Software/7/SoftwareVersion", "SoftwareVersion/31/Item_SoftwareVersion",
        "SoftwareVersion/32/Item_SoftwareVersion"]
    assert session.captured()[1]["query"] == {"range": "0-9"}


def test_get_installations_without_versions_reads_no_installation(session: GlpiMock) -> None:
    """A software without versions has no installation request."""
    session.override("GET", "Software/7/SoftwareVersion", 200, [])
    assert assets.Software.get_installations(7) == []
    assert len(session.captured()) == 1


def test_computer_keeps_the_phase_04_names(session: GlpiMock) -> None:
    """The aliases of the 0.1 API request the same sub-items as the capability methods."""
    assets.Computer.get_operating_system(1)
    assets.Computer.get_softwares(1)
    assets.Computer.get_processors(1)
    assets.Computer.get_memories(1)
    assets.Computer.get_hard_drives(1)
    assert [c["path"] for c in session.captured()] == [
        "Computer/1/Item_OperatingSystem", "Computer/1/Item_SoftwareVersion", "Computer/1/Item_DeviceProcessor",
        "Computer/1/Item_DeviceMemory", "Computer/1/Item_DeviceHardDrive"]


# Every capability reader and the sub-itemtype it must request (literals from the GLPI 10 sources)
READERS = {
    "get_infocom": "Infocom", "get_network_ports": "NetworkPort", "get_contracts": "Contract_Item",
    "get_documents": "Document_Item", "get_certificates": "Certificate_Item", "get_domains": "Domain_Item",
    "get_appliances": "Appliance_Item", "get_clusters": "Item_Cluster", "get_operating_systems": "Item_OperatingSystem",
    "get_disks": "Item_Disk", "get_sim_cards": "Item_DeviceSimcard", "get_racks": "Item_Rack",
    "get_remote_managements": "Item_RemoteManagement", "get_reservation_items": "ReservationItem",
    "get_tickets": "Item_Ticket", "get_notes": "Notepad", "get_logs": "Log",
    "get_software_versions": "Item_SoftwareVersion", "get_software_licenses": "Item_SoftwareLicense",
}


@pytest.mark.parametrize("method", sorted(READERS))
def test_every_reader_requests_its_sub_itemtype(session: GlpiMock, method: str) -> None:
    """Each capability reader (on an asset that has it) asks for the right sub-itemtype."""
    getattr(assets.Computer, method)(3)
    assert [c["path"] for c in session.captured()] == [f"Computer/3/{READERS[method]}"]


def test_notes_only_where_glpi_enables_the_notepad() -> None:
    """``$usenotepad`` is set for the physical IT assets and models, not for racks, cables or PDUs."""
    with_notes = {"Computer", "Monitor", "NetworkEquipment", "Peripheral", "Phone", "Printer", "Software",
                  "CartridgeItem", "ConsumableItem"}
    for name in assets.__all__:
        assert hasattr(getattr(assets, name), "get_notes") is (name in with_notes), name
