"""Fixes of the migrated models: no input mutation, logging, empty lists, named search fields."""

from __future__ import annotations

import copy
import logging

import pytest

from glpi_api_hero.administration import Group, User
from glpi_api_hero.assets import Computer
from glpi_api_hero.assistance import Ticket
from glpi_api_hero.core.constants import ActorType
from glpi_api_hero.dropdowns import Location
from tests.conftest import GlpiMock

TICKET_WRITERS = [
    ("add_followup", (10, {"content": "x"})),
    ("update_followup", (40, {"content": "x"})),
    ("add_solution", (10, {"content": "x"})),
    ("update_solution", (50, {"content": "x"})),
    ("add_validation", (10, {"users_id_validate": 2})),
    ("update_validation", (60, {"status": 2})),
    ("add_task", (10, {"content": "x"})),
    ("update_task", (70, {"state": 2})),
    ("add_cost", (10, {"name": "x", "cost_fixed": 5})),
    ("update_cost", (80, {"cost_fixed": 6})),
]


@pytest.mark.parametrize(("method", "args"), TICKET_WRITERS, ids=[name for name, _ in TICKET_WRITERS])
def test_ticket_writers_do_not_modify_the_input(session: GlpiMock, method: str, args: tuple) -> None:
    """The dict given by the caller is left as it was.

    Args:
        session: Simulator with an open session.
        method: Ticket method name.
        args: Its arguments (the last one is the data dict).
    """
    before = copy.deepcopy(args)
    getattr(Ticket, method)(*args)
    assert args == before


def test_update_from_list_warns_through_logging(session: GlpiMock, caplog: pytest.LogCaptureFixture,
                                                capsys: pytest.CaptureFixture[str]) -> None:
    """An empty server answer is reported with ``logging.warning``, never printed.

    Args:
        session: Simulator with an open session.
        caplog: Log capture.
        capsys: Output capture.
    """
    session.override("GET", "Location", 200, [])
    with caplog.at_level(logging.WARNING, logger="glpi_api_hero"):
        Location.update_from_list([{"name": "Room 1", "code": "R1"}])
    assert "no Location" in caplog.text
    assert capsys.readouterr().out == ""


def test_update_from_list_duplicate_entry_is_skipped_with_a_warning(session: GlpiMock,
                                                                   caplog: pytest.LogCaptureFixture) -> None:
    """A duplicate the API could not find is skipped, logged and returned as ``skipped``.

    Args:
        session: Simulator with an open session.
        caplog: Log capture.
    """
    session.override("GET", "Location", 200, [])
    session.override("POST", "Location", 400, ["ERROR_GLPI_ADD", "Duplicate entry 'Hidden' for key 'unicity'"])
    with caplog.at_level(logging.WARNING, logger="glpi_api_hero"):
        results = Location.update_from_list([{"name": "Hidden", "code": "H01"}])
    assert results == [{"skipped": True, "name": "Hidden"}]
    assert "already exists" in caplog.text


def test_update_from_list_empty_list_sends_no_request(session: GlpiMock) -> None:
    """Nothing to process: an empty list returns ``[]`` without any request.

    Args:
        session: Simulator with an open session.
    """
    session.reset_calls()
    assert Location.update_from_list([]) == []
    assert Location.add_from_list([]) == []
    assert session.captured() == []


def test_models_use_named_search_fields(session: GlpiMock) -> None:
    """Search criteria use the class constants (ids of GLPI 10 rawSearchOptions).

    Args:
        session: Simulator with an open session.
    """
    session.reset_calls()
    User.get_tickets(2, actor_type=ActorType.OBSERVER)
    Group.get_tickets(5, actor_type=ActorType.REQUESTER)
    Computer.get_by_inventory_number("INV-1")
    Location.get_users(7)
    fields = [request["query"]["criteria[0][field]"] for request in session.captured()]
    assert fields == [str(Ticket.SEARCH_FIELD_OBSERVER), str(Ticket.SEARCH_FIELD_REQUESTER_GROUP),
                      str(Computer.SEARCH_FIELD_INVENTORY_NUMBER), str(User.SEARCH_FIELD_LOCATION)]


def test_search_field_constants_match_glpi_10() -> None:
    """The ids are the ones checked in the GLPI 10 source and in the lab instance."""
    assert (Ticket.SEARCH_FIELD_REQUESTER, Ticket.SEARCH_FIELD_ASSIGNED, Ticket.SEARCH_FIELD_OBSERVER) == (4, 5, 66)
    assert (Ticket.SEARCH_FIELD_REQUESTER_GROUP, Ticket.SEARCH_FIELD_ASSIGNED_GROUP,
            Ticket.SEARCH_FIELD_OBSERVER_GROUP) == (71, 8, 65)
    ids = (Location.SEARCH_FIELD_COMPLETE_NAME, Location.SEARCH_FIELD_NAME, Location.SEARCH_FIELD_PARENT)
    assert ids == (1, 14, 13)
    assert User.SEARCH_FIELD_LOCATION == Computer.SEARCH_FIELD_LOCATION == 3


def test_add_from_list_keeps_the_location_and_entity_of_the_record(session: GlpiMock) -> None:
    """Defaults apply only when the record (or the mapper) does not set the parent and the entity.

    Args:
        session: Simulator with an open session.
    """
    session.reset_calls()
    Location.add_from_list([{"name": "A", "locations_id": 12, "entities_id": 5}, {"name": "B"}], 3, 4)
    body = session.captured()[0]["body"]["input"]
    assert body == [{"name": "A", "locations_id": 12, "entities_id": 5},
                    {"name": "B", "locations_id": 3, "entities_id": 4}]


def test_group_delete_user_reads_the_whole_membership(session: GlpiMock) -> None:
    """The member lookup asks for a wide range, so members beyond the first page are found.

    Args:
        session: Simulator with an open session.
    """
    session.reset_calls()
    Group.delete_user(5, 7)
    assert session.captured()[0]["query"]["range"] == "0-9999"
