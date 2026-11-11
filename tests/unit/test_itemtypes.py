"""Registry of the models: subpackage, class and GLPI itemtype; the generic CRUD sends the expected requests.

Each batch of models appends its rows here. Ids start with the subpackage name (``-k assets``).
"""

from __future__ import annotations

import importlib
from typing import Any

import pytest

from glpi_api_hero.core.common_dbtm import CommonDBTM
from tests.conftest import GlpiMock

# (subpackage, class name, GLPI itemtype)
REGISTRY: list[tuple[str, str, str]] = [
    ("assets", "Computer", "Computer"),
    ("assets", "Monitor", "Monitor"),
    ("assets", "Software", "Software"),
    ("assets", "NetworkEquipment", "NetworkEquipment"),
    ("assets", "Peripheral", "Peripheral"),
    ("assets", "Printer", "Printer"),
    ("assets", "CartridgeItem", "CartridgeItem"),
    ("assets", "ConsumableItem", "ConsumableItem"),
    ("assets", "Phone", "Phone"),
    ("assets", "Rack", "Rack"),
    ("assets", "Enclosure", "Enclosure"),
    ("assets", "PDU", "PDU"),
    ("assets", "PassiveDCEquipment", "PassiveDCEquipment"),
    ("assets", "Unmanaged", "Unmanaged"),
    ("assets", "Cable", "Cable"),
    ("components", "DeviceSimcard", "DeviceSimcard"),
    ("assistance", "Ticket", "Ticket"),
    ("assistance", "Change", "Change"),
    ("assistance", "Problem", "Problem"),
    ("administration", "User", "User"),
    ("administration", "Group", "Group"),
    ("dropdowns", "Location", "Location"),
]
IDS = [f"{sub}-{name}" for sub, name, _ in REGISTRY]


def _model(subpackage: str, name: str) -> type[CommonDBTM]:
    """Import a model from its subpackage.

    Args:
        subpackage: Subpackage name.
        name: Class name.

    Returns:
        The class.
    """
    return getattr(importlib.import_module(f"glpi_api_hero.{subpackage}"), name)


@pytest.mark.parametrize(("subpackage", "name", "itemtype"), REGISTRY, ids=IDS)
def test_model_has_the_expected_itemtype(subpackage: str, name: str, itemtype: str) -> None:
    """Every model derives from ``CommonDBTM`` and maps to its GLPI itemtype."""
    model = _model(subpackage, name)
    assert issubclass(model, CommonDBTM)
    assert model.get_class_name() == itemtype
    assert name in importlib.import_module(f"glpi_api_hero.{subpackage}").__all__


@pytest.mark.parametrize(("subpackage", "name", "itemtype"), REGISTRY, ids=IDS)
def test_generic_crud_requests(session: GlpiMock, subpackage: str, name: str, itemtype: str) -> None:
    """``get`` and ``search`` address the itemtype of the model."""
    model = _model(subpackage, name)
    model.get(5)
    model.search([{"field": 1, "searchtype": "contains", "value": "x"}])
    paths: list[Any] = [call["path"] for call in session.captured()]
    assert paths == [f"{itemtype}/5", f"search/{itemtype}"]


@pytest.mark.parametrize("subpackage", sorted({sub for sub, _, _ in REGISTRY}))
def test_every_exported_model_is_registered(subpackage: str) -> None:
    """Adding a model without a registry row fails here."""
    exported = set(importlib.import_module(f"glpi_api_hero.{subpackage}").__all__)
    registered = {name for sub, name, _ in REGISTRY if sub == subpackage}
    assert exported == registered
