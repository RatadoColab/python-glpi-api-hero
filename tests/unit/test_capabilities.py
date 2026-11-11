"""Capabilities of the assets follow the GLPI 10 ``$CFG_GLPI["<x>_types"]`` lists (data in ``tests/unit/data``)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from glpi_api_hero import administration, assets, management, tools
from glpi_api_hero.core import capabilities
from glpi_api_hero.exceptions import UnsupportedOperationError
from tests.conftest import GlpiMock

DATA = json.loads((Path(__file__).parent / "data" / "asset_capabilities.json").read_text(encoding="utf-8"))
CAPABILITIES: dict[str, dict[str, Any]] = DATA["capabilities"]
MATRIX: dict[str, list[str]] = DATA["matrix"]
EXCLUDED: dict[str, dict[str, Any]] = DATA["excluded"]
CASES = [(asset, cap) for asset in MATRIX for cap in CAPABILITIES]


def _model(name: str) -> Any:
    """Return an asset or management model by name.

    Args:
        name: Class name.

    Returns:
        The class.
    """
    for module in (assets, management, tools, administration):
        if name in module.__all__:
            return getattr(module, name)
    raise AttributeError(name)


@pytest.mark.parametrize(("asset", "capability"), CASES, ids=[f"{a}-{c}" for a, c in CASES])
def test_capability_present_or_absent(asset: str, capability: str) -> None:
    """A capability method exists exactly when GLPI lists the itemtype for it (minus the documented exclusions)."""
    model = _model(asset)
    if capability in EXCLUDED.get(asset, {}).get("capabilities", []):
        # Documented exclusion (see the reason in the data file): the mixin is deliberately not applied
        mixin_methods = {m for base in model.__mro__[1:] if base.__module__.endswith("capabilities")
                         for m in vars(base)}
        assert not set(CAPABILITIES[capability]["methods"]) & mixin_methods
        return
    for method in CAPABILITIES[capability]["methods"]:
        assert hasattr(model, method) is (capability in MATRIX[asset]), f"{asset}.{method}"


def test_matrix_covers_every_asset_and_management_class() -> None:
    """Each exported asset and management model has a row in the matrix."""
    assert sorted(MATRIX) == sorted(assets.__all__ + management.__all__ + list(DATA["other_models"]))


def test_cable_example_has_no_infocom_free_methods() -> None:
    """Cables take no network ports nor contracts (not in ``networkport_types`` / ``contract_types``)."""
    assert not hasattr(assets.Cable, "get_network_ports")
    assert not hasattr(assets.Cable, "get_contracts")
    assert hasattr(assets.Cable, "get_infocom")


def test_device_types_table_matches_the_data() -> None:
    """``ITEM_DEVICE_TYPES`` is the extracted ``itemdevice<x>_types`` table."""
    expected = {name: tuple(owners) for name, owners in DATA["device_types"].items()}
    assert capabilities.ITEM_DEVICE_TYPES == expected


def test_get_devices_one_kind(session: GlpiMock) -> None:
    """A specific component kind is one sub-item request."""
    assets.Computer.get_devices(12, "Item_DeviceProcessor")
    assert [c["path"] for c in session.captured()] == ["Computer/12/Item_DeviceProcessor"]


def test_get_devices_all_kinds_of_an_enclosure(session: GlpiMock) -> None:
    """Without a kind, only the kinds the itemtype can own are read (GLPI order: PCI, power supply, generic)."""
    rows = assets.Enclosure.get_devices(4)
    assert [c["path"] for c in session.captured()] == [
        "Enclosure/4/Item_DevicePci", "Enclosure/4/Item_DevicePowerSupply", "Enclosure/4/Item_DeviceGeneric"]
    assert {row["device_itemtype"] for row in rows} == {"Item_DevicePowerSupply", "Item_DevicePci",
                                                        "Item_DeviceGeneric"}


def test_get_devices_rejects_unknown_and_foreign_kinds(session: GlpiMock) -> None:
    """Unknown kinds are a ``ValueError`` and kinds the itemtype cannot own are unsupported; no request is sent."""
    with pytest.raises(ValueError):
        assets.Computer.get_devices(1, "Item_DeviceNope")
    with pytest.raises(UnsupportedOperationError):
        assets.Enclosure.get_devices(1, "Item_DeviceProcessor")
    assert session.captured() == []


def test_computer_can_own_a_case_component(session: GlpiMock) -> None:
    """``Item_DeviceCase`` is owned by computers only (``itemdevices_itemaffinity``)."""
    assets.Computer.get_devices(1, "Item_DeviceCase")
    assert session.captured()[0]["path"] == "Computer/1/Item_DeviceCase"
    with pytest.raises(UnsupportedOperationError):
        assets.Phone.get_devices(1, "Item_DeviceCase")


def test_get_devices_rows_always_carry_the_kind(session: GlpiMock) -> None:
    """The row shape does not depend on whether a kind was given."""
    rows = assets.Computer.get_devices(1, "Item_DeviceMemory")
    assert {row["device_itemtype"] for row in rows} == {"Item_DeviceMemory"}
