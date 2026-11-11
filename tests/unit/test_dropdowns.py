"""Dropdown models: the tree base and its users."""

from __future__ import annotations

import pytest

from glpi_api_hero.dropdowns import ITILCategory, Location, State
from tests.conftest import GlpiMock


@pytest.mark.parametrize("model", [Location, ITILCategory, State], ids=["Location", "ITILCategory", "State"])
def test_tree_lookups(session: GlpiMock, model: type) -> None:
    """Name (14), complete name (1), children and roots (13) use the CommonTreeDropdown options."""
    name = model.get_class_name()
    model.get_by_name("a")
    model.get_by_complete_name("a > b")
    model.get_children(5)
    model.get_roots()
    calls = session.captured()
    assert all(c["path"] == f"search/{name}" for c in calls)
    keys = ("criteria[0][field]", "criteria[0][searchtype]", "criteria[0][value]")
    fields = [tuple(c["query"][k] for k in keys) for c in calls]
    assert fields == [("14", "contains", "a"), ("1", "contains", "a > b"), ("13", "equals", "5"),
                      ("13", "equals", "0")]


def test_location_items_by_type(session: GlpiMock) -> None:
    """Items of any itemtype are searched by the location option (3); the itemtype is validated first."""
    Location.get_items_by_type(7, "Printer", range="0-4")
    request = session.captured()[0]
    assert request["path"] == "search/Printer"
    assert request["query"]["criteria[0][field]"] == "3"
    session.reset_calls()
    with pytest.raises(ValueError):
        Location.get_items_by_type(7, "../bad")
    assert session.captured() == []
