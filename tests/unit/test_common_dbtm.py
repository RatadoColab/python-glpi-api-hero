"""Normalized contract of ``CommonDBTM`` (one test per row of the phase 02 contract table)."""

from __future__ import annotations

import copy
import inspect

import pytest

from glpi_api_hero import CommonDBTM
from glpi_api_hero.exceptions import (
    BadRequestError,
    ConfigurationError,
    NotFoundError,
    PartialOperationError,
    PermissionDeniedError,
)
from tests.conftest import GlpiMock


class Location(CommonDBTM):
    """Test model whose itemtype is the class name."""


class Renamed(CommonDBTM):
    """Test model whose itemtype differs from the class name."""

    _glpi_name = "Ticket_User"


def _request(glpi_mock: GlpiMock, index: int = 0) -> dict:
    """Return one captured request.

    Args:
        glpi_mock: Active GLPI simulator.
        index: Position of the request.

    Returns:
        The request description.
    """
    return glpi_mock.captured()[index]


def test_every_public_method_is_a_classmethod() -> None:
    """Models are used without instances (R8)."""
    public = [name for name in vars(CommonDBTM) if not name.startswith("_")]
    assert public
    for name in public:
        assert isinstance(inspect.getattr_static(CommonDBTM, name), classmethod), name


def test_get_class_name() -> None:
    """The itemtype is the class name unless ``_glpi_name`` overrides it."""
    assert Location.get_class_name() == "Location"
    assert Renamed.get_class_name() == "Ticket_User"


def test_get(session: GlpiMock) -> None:
    """``get`` returns a dict and converts booleans.

    Args:
        session: Simulator with an open session.
    """
    assert Location.get(7, expand_dropdowns=True)["id"] == 7
    assert _request(session)["path"] == "Location/7"
    assert _request(session)["query"] == {"expand_dropdowns": "true"}


def test_get_missing_raises_not_found(session: GlpiMock) -> None:
    """``get`` of a missing item raises ``NotFoundError`` (D8).

    Args:
        session: Simulator with an open session.
    """
    session.override("GET", "Location/9", 404, ["ERROR_ITEM_NOT_FOUND", "Item not found"])
    with pytest.raises(NotFoundError):
        Location.get(9)


def test_get_all(session: GlpiMock) -> None:
    """``get_all`` returns a list, empty when GLPI answers something else.

    Args:
        session: Simulator with an open session.
    """
    assert [row["id"] for row in Location.get_all(range="0-49", sort=1)] == [1, 2]
    assert _request(session)["query"] == {"range": "0-49", "sort": "1"}
    session.override("GET", "Location", 200, {})
    assert Location.get_all() == []


def test_search(session: GlpiMock) -> None:
    """``search`` returns the rows and accepts forcedisplay and extra parameters.

    Args:
        session: Simulator with an open session.
    """
    rows = Location.search([{"field": 1, "searchtype": "contains", "value": "a"}], forcedisplay=[2], range="0-9")
    assert rows == [{"1": "Location-1", "2": 1}, {"1": "Location-2", "2": 2}]
    assert _request(session)["query"] == {"criteria[0][field]": "1", "criteria[0][searchtype]": "contains",
                                          "criteria[0][value]": "a", "forcedisplay[0]": "2", "range": "0-9"}
    session.override("GET", "search/Location", 200, {"totalcount": 0, "count": 0})
    assert Location.search([{"field": 1, "searchtype": "equals", "value": "none"}]) == []


def test_add_returns_the_id(session: GlpiMock) -> None:
    """``add`` sends one item and returns its id.

    Args:
        session: Simulator with an open session.
    """
    assert Location.add({"name": "a"}) == 101
    assert _request(session)["body"] == {"input": [{"name": "a"}]}


def test_add_refused_raises_bad_request(session: GlpiMock) -> None:
    """A refused addition raises ``BadRequestError``.

    Args:
        session: Simulator with an open session.
    """
    session.override("POST", "Location", 400, ["ERROR_GLPI_ADD", "Duplicate entry"])
    with pytest.raises(BadRequestError, match="Duplicate entry"):
        Location.add({"name": "a"})
    session.override("POST", "Location", 201, [{"id": False, "message": "refused"}])
    with pytest.raises(BadRequestError, match="refused"):
        Location.add({"name": "a"})


def test_add_many(session: GlpiMock) -> None:
    """``add_many`` returns the ids in input order; partial failures raise.

    Args:
        session: Simulator with an open session.
    """
    assert Location.add_many([{"name": "a"}, {"name": "b"}]) == [101, 102]
    assert _request(session)["body"] == {"input": [{"name": "a"}, {"name": "b"}]}
    session.override("POST", "Location", 207, ["ERROR_GLPI_PARTIAL_ADD",
                                               [{"id": 5, "message": ""}, {"id": False, "message": "x"}]])
    with pytest.raises(PartialOperationError):
        Location.add_many([{"name": "a"}, {"name": "b"}])


def test_update(session: GlpiMock) -> None:
    """``update`` sends the id with the fields and returns ``None``.

    Args:
        session: Simulator with an open session.
    """
    assert Location.update(7, {"comment": "x"}) is None
    request = _request(session)
    assert (request["method"], request["path"]) == ("PUT", "Location")
    assert request["body"] == {"input": [{"id": 7, "comment": "x"}]}


def test_update_missing_raises_not_found(session: GlpiMock) -> None:
    """A per-item update failure raises ``NotFoundError``.

    Args:
        session: Simulator with an open session.
    """
    session.override("PUT", "Location", 200, [{"9": False, "message": "Item not found"}])
    with pytest.raises(NotFoundError):
        Location.update(9, {"comment": "x"})


def test_update_many(session: GlpiMock) -> None:
    """``update_many`` sends every item; partial failures raise.

    Args:
        session: Simulator with an open session.
    """
    assert Location.update_many([{"id": 7, "name": "a"}, {"id": 8, "name": "b"}]) is None
    assert _request(session)["body"] == {"input": [{"id": 7, "name": "a"}, {"id": 8, "name": "b"}]}
    session.override("PUT", "Location", 207, ["ERROR_GLPI_PARTIAL_UPDATE",
                                              [{"7": True, "message": ""}, {"8": False, "message": "x"}]])
    with pytest.raises(PartialOperationError):
        Location.update_many([{"id": 7}, {"id": 8}])


def test_delete(session: GlpiMock) -> None:
    """``delete`` sends one id and the non-default flags.

    Args:
        session: Simulator with an open session.
    """
    assert Location.delete(7) is None
    assert Location.delete(8, force_purge=True, history=False) is None
    assert _request(session, 0) == {**_request(session, 0), "query": {}, "body": {"input": [{"id": 7}]}}
    assert _request(session, 1)["query"] == {"force_purge": "true", "history": "false"}


def test_delete_missing_or_forbidden(session: GlpiMock) -> None:
    """A failed single delete raises ``NotFoundError`` or ``PermissionDeniedError``.

    Args:
        session: Simulator with an open session.
    """
    session.override("DELETE", "Location", 400, ["ERROR_GLPI_DELETE", [{"9": False, "message": "Item not found"}]])
    with pytest.raises(NotFoundError, match="Item not found"):
        Location.delete(9)
    session.override("DELETE", "Location", 400, ["ERROR_GLPI_DELETE", [
        {"9": False, "message": "You don't have permission to perform this action."}]])
    with pytest.raises(PermissionDeniedError):
        Location.delete(9)


def test_delete_many(session: GlpiMock) -> None:
    """``delete_many`` sends every id; partial failures raise.

    Args:
        session: Simulator with an open session.
    """
    assert Location.delete_many([7, 8], force_purge=True) is None
    assert _request(session)["body"] == {"input": [{"id": 7}, {"id": 8}]}
    assert _request(session)["query"] == {"force_purge": "true"}
    session.override("DELETE", "Location", 207, ["ERROR_GLPI_PARTIAL_DELETE",
                                                 [{"7": True, "message": ""}, {"8": False, "message": "x"}]])
    with pytest.raises(PartialOperationError):
        Location.delete_many([7, 8])


def test_empty_bulk_sends_nothing(session: GlpiMock) -> None:
    """Empty bulk operations return immediately.

    Args:
        session: Simulator with an open session.
    """
    assert Location.add_many([]) == []
    assert Location.update_many([]) is None
    assert Location.delete_many([]) is None
    assert session.captured() == []


def test_sub_items(session: GlpiMock) -> None:
    """Sub-item read and CRUD use the ``<itemtype>/<id>/<sub>`` endpoint.

    Args:
        session: Simulator with an open session.
    """
    assert [row["id"] for row in Location.get_sub_items(7, "Log", range="0-9")] == [11, 12]
    assert Location.add_sub_item(7, "Document_Item", {"documents_id": 3}) == 201
    assert Location.update_sub_item(7, "Document_Item", 11, {"documents_id": 4}) is None
    assert Location.delete_sub_item(7, "Document_Item", 11) is None
    calls = [(r["method"], r["path"], r["body"]) for r in session.captured()]
    assert calls == [
        ("GET", "Location/7/Log", None),
        ("POST", "Location/7/Document_Item", {"input": [{"documents_id": 3}]}),
        ("PUT", "Location/7/Document_Item", {"input": [{"id": 11, "documents_id": 4}]}),
        ("DELETE", "Location/7/Document_Item", {"input": [{"id": 11}]}),
    ]


def test_search_options_and_fields(session: GlpiMock) -> None:
    """Search options, ``field_id`` and ``field_uid`` share one cached request.

    Args:
        session: Simulator with an open session.
    """
    assert Location.search_options()["1"]["uid"] == "Location.name"
    assert Location.field_id("serial") == 5
    assert Location.field_uid(80) == "Entity.completename"
    with pytest.raises(BadRequestError):
        Location.field_id("unknown")
    assert [r["path"] for r in session.captured()] == ["listSearchOptions/Location", "listSearchOptions/Location"]
    Location.search_options(raw=True)
    assert session.captured()[-1]["query"] == {"raw": ""}


def test_inputs_are_not_mutated(session: GlpiMock) -> None:
    """No method modifies the dicts or lists it receives.

    Args:
        session: Simulator with an open session.
    """
    data = {"name": "a"}
    items = [{"id": 7, "name": "b"}]
    criteria = [{"field": 1, "searchtype": "equals", "value": "o'x"}]
    before = copy.deepcopy((data, items, criteria))
    Location.add(data)
    Location.add_many(items)
    Location.update(7, data)
    Location.update_many(items)
    Location.add_sub_item(7, "Log", data)
    Location.update_sub_item(7, "Log", 1, data)
    Location.search(criteria)
    assert (data, items, criteria) == before


def test_without_session_raises_configuration_error(glpi_mock: GlpiMock) -> None:
    """Calls without an open session fail without any request.

    Args:
        glpi_mock: Active GLPI simulator.
    """
    with pytest.raises(ConfigurationError):
        Location.get(1)
    assert glpi_mock.captured() == []
