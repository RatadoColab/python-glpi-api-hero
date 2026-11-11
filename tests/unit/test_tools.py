"""Tools models: project, reminder, knowledge base, reservations."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest

from glpi_api_hero import tools
from tests.conftest import GlpiMock

READS: list[tuple[str, Callable[[], Any], str]] = [
    ("project-tasks", lambda: tools.Project.get_tasks(1), "Project/1/ProjectTask"),
    ("project-team", lambda: tools.Project.get_team(1), "Project/1/ProjectTeam"),
    ("project-items", lambda: tools.Project.get_items(1), "Project/1/Item_Project"),
    ("project-costs", lambda: tools.Project.get_costs(1), "Project/1/ProjectCost"),
    ("project-itil", lambda: tools.Project.get_itil_objects(1), "Project/1/Itil_Project"),
    ("project-contracts", lambda: tools.Project.get_contracts(1), "Project/1/Contract_Item"),
    ("knowbaseitem-items", lambda: tools.KnowbaseItem.get_items(2), "KnowbaseItem/2/KnowbaseItem_Item"),
    ("reservationitem-reservations", lambda: tools.ReservationItem.get_reservations(3),
     "ReservationItem/3/Reservation"),
]


@pytest.mark.parametrize(("call", "path"), [(c, p) for _, c, p in READS], ids=[i for i, _, _ in READS])
def test_reads(session: GlpiMock, call: Callable[[], Any], path: str) -> None:
    """Each reader is one GET on the expected sub-item."""
    call()
    assert [(r["method"], r["path"]) for r in session.captured()] == [("GET", path)]


WRITES: list[tuple[str, Callable[[], Any], str, str, dict[str, Any]]] = [
    ("project-add-task", lambda: tools.Project.add_task(1, {"name": "t"}), "POST", "ProjectTask",
     {"name": "t", "projects_id": 1}),
    ("project-update-task", lambda: tools.Project.update_task(9, {"name": "u"}), "PUT", "ProjectTask",
     {"name": "u", "id": 9}),
    ("project-delete-task", lambda: tools.Project.delete_task(9), "DELETE", "ProjectTask", {"id": 9}),
    ("project-add-team-member", lambda: tools.Project.add_team_member(1, "User", 5), "POST", "ProjectTeam",
     {"projects_id": 1, "itemtype": "User", "items_id": 5}),
    ("project-delete-team-member", lambda: tools.Project.delete_team_member(6), "DELETE", "ProjectTeam", {"id": 6}),
    ("reservation-add", lambda: tools.ReservationItem.add_reservation(3, {"begin": "2026-01-01 08:00:00"}), "POST",
     "Reservation", {"begin": "2026-01-01 08:00:00", "reservationitems_id": 3}),
    ("reservation-delete", lambda: tools.ReservationItem.delete_reservation(8), "DELETE", "Reservation", {"id": 8}),
]


@pytest.mark.parametrize(("call", "method", "path", "expected"), [w[1:] for w in WRITES], ids=[w[0] for w in WRITES])
def test_writes(session: GlpiMock, call: Callable[[], Any], method: str, path: str, expected: dict[str, Any]) -> None:
    """Writes bind the child to the parent with the column GLPI expects."""
    call()
    request = session.captured()[0]
    assert (request["method"], request["path"], request["body"]["input"][0]) == (method, path, expected)


@pytest.mark.parametrize(("model", "paths"), [
    (tools.Reminder, ["Entity_Reminder", "Group_Reminder", "Profile_Reminder", "Reminder_User"]),
    (tools.KnowbaseItem, ["Entity_KnowbaseItem", "Group_KnowbaseItem", "KnowbaseItem_Profile", "KnowbaseItem_User"]),
], ids=["reminder", "knowbaseitem"])
def test_get_targets_aggregates_the_four_relations(session: GlpiMock, model: Any, paths: list[str]) -> None:
    """Each relation is read once and every row carries ``kind`` and ``target_id``."""
    column = {0: "entities_id", 1: "groups_id", 2: "profiles_id", 3: "users_id"}
    for index, itemtype in enumerate(paths):
        session.override("GET", f"{model.get_class_name()}/4/{itemtype}", 200, [{"id": 1, column[index]: 70 + index}])
    rows = model.get_targets(4)
    assert [c["path"] for c in session.captured()] == [f"{model.get_class_name()}/4/{p}" for p in paths]
    assert [(r["kind"], r["target_id"]) for r in rows] == [("entity", 70), ("group", 71), ("profile", 72),
                                                           ("user", 73)]


def test_get_targets_without_targets_is_empty(session: GlpiMock) -> None:
    """No relation row means ``[]``."""
    for itemtype in ("Entity_Reminder", "Group_Reminder", "Profile_Reminder", "Reminder_User"):
        session.override("GET", f"Reminder/4/{itemtype}", 200, [])
    assert tools.Reminder.get_targets(4) == []


def test_writes_do_not_modify_the_input(session: GlpiMock) -> None:
    """The caller dicts stay as they were."""
    data = {"name": "t"}
    tools.Project.add_task(1, data)
    tools.Project.update_task(2, data)
    assert data == {"name": "t"}
