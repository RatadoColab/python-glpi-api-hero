"""ITIL base: every parent x resource combination sends the request GLPI 10 expects.

The expected itemtypes and columns are literal values taken from the GLPI 10 sources
(``src/Ticket_User.php``, ``src/Change_Problem.php``...), not derived from the library constants.
"""

from __future__ import annotations

import copy
import inspect
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from glpi_api_hero.assistance import Change, Problem, Ticket
from glpi_api_hero.core.common_itil import CommonITILObject
from glpi_api_hero.core.constants import ActorKind, ActorType, LinkType
from glpi_api_hero.exceptions import NotFoundError, UnsupportedOperationError
from tests.conftest import GlpiMock

ROOT = Path(__file__).resolve().parents[2]

# Itemtypes and columns of each parent (GLPI 10 sources)
PARENTS: dict[str, dict[str, Any]] = {
    "Ticket": {
        "cls": Ticket, "fk": "tickets_id", "task": "TicketTask", "validation": "TicketValidation",
        "user": "Ticket_User", "group": "Group_Ticket", "supplier": "Supplier_Ticket",
        "item": "Item_Ticket", "cost": "TicketCost",
    },
    "Change": {
        "cls": Change, "fk": "changes_id", "task": "ChangeTask", "validation": "ChangeValidation",
        "user": "Change_User", "group": "Change_Group", "supplier": "Change_Supplier",
        "item": "Change_Item", "cost": "ChangeCost",
    },
    "Problem": {
        "cls": Problem, "fk": "problems_id", "task": "ProblemTask", "validation": None,
        "user": "Problem_User", "group": "Group_Problem", "supplier": "Problem_Supplier",
        "item": "Item_Problem", "cost": "ProblemCost",
    },
}
PARENT_IDS = list(PARENTS)

# Link matrix: parent -> method -> (link itemtype, own column, other column); None when unsupported
LINKS: dict[str, dict[str, tuple[str, str, str] | None]] = {
    "Ticket": {"tickets": ("Ticket_Ticket", "tickets_id_1", "tickets_id_2"),
               "problems": ("Problem_Ticket", "tickets_id", "problems_id"),
               "changes": ("Change_Ticket", "tickets_id", "changes_id")},
    "Change": {"tickets": ("Change_Ticket", "changes_id", "tickets_id"),
               "problems": ("Change_Problem", "changes_id", "problems_id"),
               "changes": None},
    "Problem": {"tickets": ("Problem_Ticket", "problems_id", "tickets_id"),
                "problems": None,
                "changes": ("Change_Problem", "problems_id", "changes_id")},
}
LINK_CALLS = {"tickets": ("link_ticket", "get_linked_tickets"), "problems": ("link_problem", "get_linked_problems"),
              "changes": ("link_change", "get_linked_changes")}


def _only(glpi_mock: GlpiMock) -> dict[str, Any]:
    """Return the single captured request.

    Args:
        glpi_mock: Active GLPI simulator.

    Returns:
        The request description.
    """
    calls = glpi_mock.captured()
    assert len(calls) == 1
    return calls[0]


def _input(request: dict[str, Any]) -> dict[str, Any]:
    """Return the first ``input`` item of a write request.

    Args:
        request: Request description.

    Returns:
        The sent fields.
    """
    return request["body"]["input"][0]


# --------------------------------------------------------------------- structure
@pytest.mark.parametrize("name", PARENT_IDS)
def test_parents_inherit_the_itil_base(name: str) -> None:
    """Ticket, Change and Problem share ``CommonITILObject``."""
    assert issubclass(PARENTS[name]["cls"], CommonITILObject)
    assert PARENTS[name]["cls"].get_class_name() == name


def test_every_public_method_is_a_classmethod() -> None:
    """Models are used without instances (R8)."""
    public = [n for n in vars(CommonITILObject) if not n.startswith("_") and n.upper() != n]
    assert public
    for method in public:
        assert isinstance(inspect.getattr_static(CommonITILObject, method), classmethod), method


def test_legacy_sub_item_modules_are_gone() -> None:
    """The provisional sub-item classes of phase 04.1 no longer exist."""
    package = ROOT / "src" / "glpi_api_hero"
    assert not (package / "core" / "_legacy_children.py").exists()
    for module in ("actor", "item", "task", "linked_ticket", "itilfollowup", "itilsolution", "ticket_validation",
                   "cluster", "network_equipment"):
        assert not (package / f"{module}.py").exists(), module


# ------------------------------------------------------------ parent x resource
@pytest.mark.parametrize("name", PARENT_IDS)
def test_followup_and_solution_are_polymorphic(session: GlpiMock, name: str) -> None:
    """Follow-ups and solutions bind to the parent with ``itemtype`` + ``items_id``."""
    parent = PARENTS[name]["cls"]
    for resource, itemtype in (("followup", "ITILFollowup"), ("solution", "ITILSolution")):
        session.reset_calls()
        assert getattr(parent, f"add_{resource}")(7, {"content": "x"}) == 101
        request = _only(session)
        assert (request["method"], request["path"]) == ("POST", itemtype)
        assert _input(request) == {"content": "x", "itemtype": name, "items_id": 7}
        session.reset_calls()
        getattr(parent, f"get_{resource}s")(7)
        assert _only(session)["path"] == f"{name}/7/{itemtype}"
        session.reset_calls()
        getattr(parent, f"update_{resource}")(40, {"content": "y"})
        request = _only(session)
        assert (request["method"], request["path"], _input(request)) == ("PUT", itemtype, {"content": "y", "id": 40})
        session.reset_calls()
        getattr(parent, f"delete_{resource}")(40)
        request = _only(session)
        assert (request["method"], request["path"], _input(request)) == ("DELETE", itemtype, {"id": 40})


@pytest.mark.parametrize("resource", ["task", "cost"])
@pytest.mark.parametrize("name", PARENT_IDS)
def test_owned_children_use_the_parent_foreign_key(session: GlpiMock, name: str, resource: str) -> None:
    """Tasks and costs carry ``tickets_id``/``changes_id``/``problems_id``."""
    parent, spec = PARENTS[name]["cls"], PARENTS[name]
    itemtype, fk = spec[resource], spec["fk"]
    assert getattr(parent, f"add_{resource}")(7, {"name": "x"}) == 101
    request = _only(session)
    assert (request["method"], request["path"], _input(request)) == ("POST", itemtype, {"name": "x", fk: 7})
    session.reset_calls()
    getattr(parent, f"get_{resource}s")(7)
    assert _only(session)["path"] == f"{name}/7/{itemtype}"
    session.reset_calls()
    getattr(parent, f"update_{resource}")(9, {"name": "y"})
    request = _only(session)
    assert (request["method"], request["path"], _input(request)) == ("PUT", itemtype, {"name": "y", "id": 9})
    session.reset_calls()
    getattr(parent, f"delete_{resource}")(9)
    request = _only(session)
    assert (request["method"], request["path"], _input(request)) == ("DELETE", itemtype, {"id": 9})


@pytest.mark.parametrize("name", ["Ticket", "Change"])
def test_validations_use_the_parent_foreign_key(session: GlpiMock, name: str) -> None:
    """Ticket and Change validations carry the parent column."""
    parent, spec = PARENTS[name]["cls"], PARENTS[name]
    assert parent.add_validation(7, {"users_id_validate": 2}) == 101
    request = _only(session)
    assert (request["path"], _input(request)) == (spec["validation"], {"users_id_validate": 2, spec["fk"]: 7})
    session.reset_calls()
    parent.get_validations(7)
    assert _only(session)["path"] == f"{name}/7/{spec['validation']}"
    session.reset_calls()
    parent.update_validation(60, {"status": 2})
    assert (_only(session)["method"], _only(session)["path"]) == ("PUT", spec["validation"])
    session.reset_calls()
    parent.delete_validation(60)
    assert (_only(session)["method"], _only(session)["path"]) == ("DELETE", spec["validation"])


def test_unsupported_validations_on_problem(session: GlpiMock) -> None:
    """A Problem has no validations: every validation method fails before any request."""
    calls: list[Callable[[], Any]] = [
        lambda: Problem.add_validation(1, {}),
        lambda: Problem.update_validation(1, {}),
        lambda: Problem.delete_validation(1),
        lambda: Problem.get_validations(1),
    ]
    for call in calls:
        with pytest.raises(UnsupportedOperationError):
            call()
    assert session.captured() == []


@pytest.mark.parametrize("name", PARENT_IDS)
def test_items_link_assets_with_the_parent_foreign_key(session: GlpiMock, name: str) -> None:
    """The asset keeps its own ``itemtype``/``items_id``; the parent goes in its column."""
    parent, spec = PARENTS[name]["cls"], PARENTS[name]
    assert parent.add_item(7, "Computer", 3) == 101
    request = _only(session)
    assert (request["path"], _input(request)) == (spec["item"], {spec["fk"]: 7, "itemtype": "Computer", "items_id": 3})
    session.reset_calls()
    parent.get_items(7)
    assert _only(session)["path"] == f"{name}/7/{spec['item']}"
    session.reset_calls()
    parent.delete_item(80)
    assert (_only(session)["method"], _only(session)["path"]) == ("DELETE", spec["item"])


@pytest.mark.parametrize("name", PARENT_IDS)
def test_documents_are_polymorphic(session: GlpiMock, name: str) -> None:
    """Documents attach through ``Document_Item`` with the parent itemtype and id."""
    parent = PARENTS[name]["cls"]
    assert parent.add_document(7, 5) == 101
    request = _only(session)
    assert (request["path"], _input(request)) == ("Document_Item",
                                                  {"documents_id": 5, "itemtype": name, "items_id": 7})
    session.reset_calls()
    parent.get_documents(7)
    assert _only(session)["path"] == f"{name}/7/Document_Item"
    session.reset_calls()
    parent.delete_document(33)
    assert (_only(session)["method"], _only(session)["path"]) == ("DELETE", "Document_Item")


# ------------------------------------------------------------------------ actors
@pytest.mark.parametrize("kind", list(ActorKind))
@pytest.mark.parametrize("name", PARENT_IDS)
def test_actors_by_kind(session: GlpiMock, name: str, kind: ActorKind) -> None:
    """Each actor kind goes to its own link itemtype and column."""
    parent, spec = PARENTS[name]["cls"], PARENTS[name]
    column = {"user": "users_id", "group": "groups_id", "supplier": "suppliers_id"}[kind.value]
    assert parent.add_actor(7, kind, 5, ActorType.ASSIGNED) == 101
    request = _only(session)
    expected = {spec["fk"]: 7, column: 5, "type": 2}
    if kind is not ActorKind.GROUP:
        expected["use_notification"] = 1
    assert (request["path"], _input(request)) == (spec[kind.value], expected)
    session.reset_calls()
    parent.delete_actor(90, kind)
    request = _only(session)
    assert (request["method"], request["path"], _input(request)) == ("DELETE", spec[kind.value], {"id": 90})


@pytest.mark.parametrize("name", PARENT_IDS)
def test_get_actors_aggregates_the_three_kinds(session: GlpiMock, name: str) -> None:
    """``get_actors`` reads users, groups and suppliers and tags each row with its kind."""
    parent, spec = PARENTS[name]["cls"], PARENTS[name]
    rows = parent.get_actors(7)
    assert [call["path"] for call in session.captured()] == [
        f"{name}/7/{spec['user']}", f"{name}/7/{spec['group']}", f"{name}/7/{spec['supplier']}"]
    assert [row["kind"] for row in rows] == ["user", "user", "group", "group", "supplier", "supplier"]


def test_actor_options_and_validation(session: GlpiMock) -> None:
    """Notification, e-mail and invalid values."""
    Ticket.add_actor(7, "user", 0, 1, use_notification=False, alternative_email="a@example.org")
    assert _input(_only(session)) == {"tickets_id": 7, "users_id": 0, "type": 1, "use_notification": 0,
                                      "alternative_email": "a@example.org"}
    session.reset_calls()
    with pytest.raises(ValueError):
        Ticket.add_actor(7, "robot", 1, 1)
    with pytest.raises(ValueError):
        Ticket.add_actor(7, ActorKind.USER, 1, 9)
    with pytest.raises(ValueError):
        Ticket.add_actor(7, ActorKind.GROUP, 1, 1, alternative_email="a@example.org")
    with pytest.raises(ValueError):
        Ticket.delete_actor(1, "robot")
    assert session.captured() == []


def test_get_actors_does_not_modify_the_rows_it_receives(session: GlpiMock) -> None:
    """The rows of the connector are copied before the ``kind`` key is added."""
    rows = [{"id": 1, "tickets_id": 7}]
    session.override("GET", "Ticket/7/Ticket_User", 200, rows)
    result = Ticket.get_actors(7)
    assert result[0]["kind"] == "user"
    assert rows == [{"id": 1, "tickets_id": 7}]


# --------------------------------------------------------------------- solution
@pytest.mark.parametrize("name", PARENT_IDS)
def test_approve_and_refuse_solution(session: GlpiMock, name: str) -> None:
    """Approval and refusal are follow-ups with ``add_close`` / ``add_reopen`` (``ITILFollowup.php``)."""
    parent = PARENTS[name]["cls"]
    assert parent.approve_solution(7) == 101
    assert _input(_only(session)) == {"add_close": 1, "itemtype": name, "items_id": 7}
    session.reset_calls()
    parent.approve_solution(7, "thanks")
    assert _input(_only(session)) == {"add_close": 1, "content": "thanks", "itemtype": name, "items_id": 7}
    session.reset_calls()
    assert parent.refuse_solution(7, "still broken") == 101
    assert _input(_only(session)) == {"add_reopen": 1, "content": "still broken", "itemtype": name, "items_id": 7}


@pytest.mark.parametrize("comment", ["", "   ", None])
def test_refuse_solution_requires_a_comment(session: GlpiMock, comment: Any) -> None:
    """GLPI rejects a refusal without reason, so it is refused before the request."""
    with pytest.raises(ValueError):
        Ticket.refuse_solution(7, comment)
    assert session.captured() == []


# ------------------------------------------------------------------------ links
@pytest.mark.parametrize("target", ["tickets", "problems", "changes"])
@pytest.mark.parametrize("name", PARENT_IDS)
def test_link_matrix(session: GlpiMock, name: str, target: str) -> None:
    """Each parent x target combination writes the right link itemtype and columns, or is unsupported."""
    parent, spec = PARENTS[name]["cls"], LINKS[name][target]
    link_call, get_call = LINK_CALLS[target]
    if spec is None:
        with pytest.raises(UnsupportedOperationError):
            getattr(parent, link_call)(7, 9)
        with pytest.raises(UnsupportedOperationError):
            getattr(parent, get_call)(7)
        assert session.captured() == []
        return
    link_itemtype, own, other = spec
    assert getattr(parent, link_call)(7, 9) == 101
    request = _only(session)
    expected = {own: 7, other: 9}
    if link_itemtype == "Ticket_Ticket":
        expected["link"] = 1
    assert (request["path"], _input(request)) == (link_itemtype, expected)


@pytest.mark.parametrize("link", list(LinkType))
def test_link_ticket_relation_types_on_a_ticket(session: GlpiMock, link: LinkType) -> None:
    """Ticket to ticket links carry the relation type (``Ticket_Ticket::LINK_TO`` = 1 ... ``PARENT_OF`` = 4)."""
    Ticket.link_ticket(7, 9, link)
    assert _input(_only(session))["link"] == link.value


@pytest.mark.parametrize("name", ["Change", "Problem"])
def test_link_ticket_relation_type_is_rejected_outside_tickets(session: GlpiMock, name: str) -> None:
    """Only Ticket links have a relation type."""
    parent = PARENTS[name]["cls"]
    with pytest.raises(ValueError):
        parent.link_ticket(7, 9, LinkType.DUPLICATE)
    assert session.captured() == []
    parent.link_ticket(7, 9, LinkType.LINKED)
    assert "link" not in _input(_only(session))


def test_link_ticket_rejects_an_invalid_relation_type(session: GlpiMock) -> None:
    """An unknown relation type fails before the request."""
    with pytest.raises(ValueError):
        Ticket.link_ticket(7, 9, 9)  # type: ignore[arg-type]
    assert session.captured() == []


@pytest.mark.parametrize("name", ["Change", "Problem"])
def test_get_links_filtered_by_glpi_for_change_and_problem(session: GlpiMock, name: str) -> None:
    """Change and Problem links are read as sub-items (GLPI filters them by ``changes_id``/``problems_id``)."""
    parent = PARENTS[name]["cls"]
    parent.get_linked_tickets(7)
    link_itemtype = LINKS[name]["tickets"][0]  # type: ignore[index]
    assert _only(session)["path"] == f"{name}/7/{link_itemtype}"


def test_get_linked_tickets_of_a_ticket_filters_both_sides_exactly(session: GlpiMock) -> None:
    """``Ticket_Ticket`` has no ``tickets_id`` column, so rows are searched per column and filtered here.

    The text search also matches ids that merely contain the number (10 inside 100): they are dropped.
    """
    rows = [{"id": 5, "tickets_id_1": 10, "tickets_id_2": 11}, {"id": 6, "tickets_id_1": 12, "tickets_id_2": 10},
            {"id": 7, "tickets_id_1": 100, "tickets_id_2": 101}]
    session.override("GET", "Ticket_Ticket", 200, rows)
    assert [row["id"] for row in Ticket.get_linked_tickets(10)] == [5, 6]
    queries = [call["query"] for call in session.captured()]
    assert queries == [{"range": "0-9999", "searchText[tickets_id_1]": "^10$"},
                       {"range": "0-9999", "searchText[tickets_id_2]": "^10$"}]


@pytest.mark.parametrize(("name", "link_itemtype"), [
    ("Ticket", "Ticket_Ticket"), ("Ticket", "Problem_Ticket"), ("Ticket", "Change_Ticket"),
    ("Change", "Change_Ticket"), ("Change", "Change_Problem"),
    ("Problem", "Problem_Ticket"), ("Problem", "Change_Problem"),
])
def test_unlink_valid_link_itemtypes(session: GlpiMock, name: str, link_itemtype: str) -> None:
    """The link row is deleted from its own itemtype."""
    PARENTS[name]["cls"].unlink(link_itemtype, 95)
    request = _only(session)
    assert (request["method"], request["path"], _input(request)) == ("DELETE", link_itemtype, {"id": 95})


@pytest.mark.parametrize(("name", "link_itemtype"), [
    ("Change", "Ticket_Ticket"), ("Change", "Problem_Ticket"), ("Problem", "Change_Ticket"),
    ("Problem", "Ticket_Ticket"), ("Ticket", "Change_Problem"), ("Ticket", "Computer"),
])
def test_unsupported_unlink_itemtypes(session: GlpiMock, name: str, link_itemtype: str) -> None:
    """A link itemtype the parent does not have is refused before any request."""
    with pytest.raises(UnsupportedOperationError):
        PARENTS[name]["cls"].unlink(link_itemtype, 95)
    assert session.captured() == []


# ------------------------------------------------------------------ search by actor
@pytest.mark.parametrize("name", PARENT_IDS)
def test_search_by_actor_fields(session: GlpiMock, name: str) -> None:
    """The actor search ids come from ``CommonITILObject::rawSearchOptions`` (shared by the three parents)."""
    parent = PARENTS[name]["cls"]
    expected = [("get_by_requester", 4), ("get_by_assigned", 5), ("get_by_observer", 66)]
    for method, field in expected:
        session.reset_calls()
        getattr(parent, method)(3)
        request = _only(session)
        assert request["path"] == f"search/{name}"
        assert request["query"] == {"criteria[0][field]": str(field), "criteria[0][searchtype]": "equals",
                                    "criteria[0][value]": "3"}
    groups = [(ActorType.REQUESTER, 71), (ActorType.ASSIGNED, 8), (ActorType.OBSERVER, 65)]
    for actor_type, field in groups:
        session.reset_calls()
        parent.get_by_group(4, actor_type)
        assert _only(session)["query"]["criteria[0][field]"] == str(field)


def test_search_by_group_rejects_an_invalid_role(session: GlpiMock) -> None:
    """An unknown role fails before the request."""
    with pytest.raises(ValueError):
        Ticket.get_by_group(4, 9)  # type: ignore[arg-type]
    assert session.captured() == []


def test_search_by_actor_forwards_extra_parameters(session: GlpiMock) -> None:
    """Extra parameters reach the search request."""
    Ticket.get_by_requester(3, range="0-9")
    assert _only(session)["query"]["range"] == "0-9"


# ---------------------------------------------------------------- Ticket only
def test_get_satisfaction(session: GlpiMock) -> None:
    """The survey is the first row of ``TicketSatisfaction``; no row means ``NotFoundError``."""
    session.override("GET", "Ticket/7/TicketSatisfaction", 200, [{"id": 3, "tickets_id": 7, "satisfaction": 4}])
    assert Ticket.get_satisfaction(7)["satisfaction"] == 4
    session.override("GET", "Ticket/7/TicketSatisfaction", 200, [])
    with pytest.raises(NotFoundError):
        Ticket.get_satisfaction(7)


def test_change_and_problem_have_no_satisfaction() -> None:
    """Satisfaction surveys exist only for tickets."""
    assert not hasattr(Change, "get_satisfaction")
    assert not hasattr(Problem, "get_satisfaction")


# -------------------------------------------------------------------- no mutation
DICT_WRITERS: list[tuple[str, tuple[Any, ...]]] = [
    ("add_followup", (7, {"content": "x"})),
    ("update_followup", (40, {"content": "x"})),
    ("add_solution", (7, {"content": "x"})),
    ("update_solution", (50, {"content": "x"})),
    ("add_task", (7, {"content": "x"})),
    ("update_task", (70, {"state": 2})),
    ("add_validation", (7, {"users_id_validate": 2})),
    ("update_validation", (60, {"status": 2})),
    ("add_cost", (7, {"name": "x"})),
    ("update_cost", (80, {"name": "y"})),
]


@pytest.mark.parametrize("name", ["Ticket", "Change"])
@pytest.mark.parametrize(("method", "args"), DICT_WRITERS, ids=[m for m, _ in DICT_WRITERS])
def test_no_input_mutation(session: GlpiMock, name: str, method: str, args: tuple[Any, ...]) -> None:
    """The dict given by the caller is left as it was, for every parent that supports the method."""
    before = copy.deepcopy(args)
    getattr(PARENTS[name]["cls"], method)(*args)
    assert args == before


@pytest.mark.parametrize("method", ["add_followup", "add_solution", "add_task", "add_cost"])
def test_no_input_mutation_on_problem(session: GlpiMock, method: str) -> None:
    """Problem children share the same guarantee."""
    data = {"content": "x"}
    getattr(Problem, method)(7, data)
    assert data == {"content": "x"}


def test_parent_binding_wins_over_the_caller_fields(session: GlpiMock) -> None:
    """A stale ``tickets_id`` or ``items_id`` in the data cannot attach the child to another parent."""
    Ticket.add_task(7, {"content": "x", "tickets_id": 999})
    assert _input(_only(session))["tickets_id"] == 7
    session.reset_calls()
    Ticket.add_followup(7, {"content": "x", "items_id": 999, "itemtype": "Change"})
    assert _input(_only(session)) == {"content": "x", "items_id": 7, "itemtype": "Ticket"}


def test_search_followups_searches_the_followup_itemtype(session: GlpiMock) -> None:
    """The search engine runs on ``ITILFollowup`` with the given criteria."""
    Ticket.search_followups([{"field": 1, "searchtype": "contains", "value": "x"}], range="0-4")
    request = _only(session)
    assert request["path"] == "search/ITILFollowup"
    # Index 0 is the parent itemtype restriction; the caller criterion follows it
    assert request["query"]["criteria[1][value]"] == "x"
    assert request["query"]["range"] == "0-4"


def test_search_followups_is_restricted_to_the_parent_itemtype(session: GlpiMock) -> None:
    """The first criterion is ``itemtype equals <parent>`` and the user criteria follow it joined by AND."""
    criteria = [{"field": 1, "searchtype": "contains", "value": "x", "link": "OR"},
                {"field": 3, "searchtype": "contains", "value": "2026", "link": "OR"}]
    Ticket.search_followups(criteria)
    query = _only(session)["query"]
    assert query["criteria[0][field]"] == "6"
    assert query["criteria[0][searchtype]"] == "equals"
    assert query["criteria[0][value]"] == "Ticket"
    assert query["criteria[1][field]"] == "1"
    assert query["criteria[1][link]"] == "AND"
    assert query["criteria[2][field]"] == "3"
    assert query["criteria[2][link]"] == "OR"
    # The caller's list is left untouched
    assert criteria[0]["link"] == "OR"
    assert len(criteria) == 2


def test_search_followups_without_criteria_still_filters_by_parent(session: GlpiMock) -> None:
    """Change and Problem restrict to their own itemtype, even with no extra criteria."""
    for model, itemtype in ((Change, "Change"), (Problem, "Problem")):
        session.reset_calls()
        model.search_followups()
        query = _only(session)["query"]
        assert query["criteria[0][value]"] == itemtype
        assert "criteria[1][field]" not in query


def test_get_linked_tickets_keeps_the_anchored_search_when_params_collide(session: GlpiMock) -> None:
    """A caller ``searchText`` cannot replace the filter; ``range`` can be narrowed."""
    Ticket.get_linked_tickets(10, searchText={"tickets_id_1": "5"}, range="0-4")
    queries = [call["query"] for call in session.captured()]
    assert queries[0] == {"range": "0-4", "searchText[tickets_id_1]": "^10$"}


def test_approve_solution_ignores_a_blank_comment(session: GlpiMock) -> None:
    """A blank comment is not sent, so GLPI writes its own approval text."""
    Ticket.approve_solution(7, "   ")
    assert "content" not in _input(_only(session))


def test_get_actors_copies_the_rows_of_the_connector(monkeypatch: pytest.MonkeyPatch) -> None:
    """The very list objects returned by the lookup are left untouched (``kind`` goes into copies)."""
    shared = [{"id": 1}]
    monkeypatch.setattr(Ticket, "get_sub_items", classmethod(lambda cls, *args, **kwargs: shared))
    result = Ticket.get_actors(7)
    assert shared == [{"id": 1}]
    assert [row["kind"] for row in result] == ["user", "group", "supplier"]
