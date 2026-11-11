"""Base of the ITIL objects (Ticket, Change and Problem) with their sub-items exposed as methods.

Sub-items (follow-ups, solutions, tasks, validations, actors, linked assets, costs, documents and
links between ITIL objects) have no public class: each one is a method of the parent. The itemtype
of every child is declared by the concrete parent through class attributes.

Example::

    from glpi_api_hero.assistance import Ticket
    from glpi_api_hero.core.constants import ActorKind, ActorType

    ticket_id = Ticket.add({"name": "Printer down", "content": "Paper jam"})
    Ticket.add_followup(ticket_id, {"content": "Technician on the way"})
    Ticket.add_actor(ticket_id, ActorKind.GROUP, 5, ActorType.ASSIGNED)
"""

from __future__ import annotations

from typing import Any, ClassVar

from glpi_api_hero.core.common_dbtm import CommonDBTM
from glpi_api_hero.core.constants import ActorKind, ActorType, LinkType
from glpi_api_hero.exceptions import UnsupportedOperationError

# Columns of the actor tables that hold the id of the actor, by kind
_ACTOR_FIELDS = {ActorKind.USER: "users_id", ActorKind.GROUP: "groups_id", ActorKind.SUPPLIER: "suppliers_id"}


class CommonITILObject(CommonDBTM):
    """Shared behavior of Ticket, Change and Problem.

    Attributes:
        _task_itemtype: Task itemtype (``TicketTask``...).
        _validation_itemtype: Validation itemtype, or ``None`` when the parent has no validations.
        _actor_itemtypes: Actor link itemtype by actor kind.
        _item_link_itemtype: Itemtype that links assets to the parent (``Item_Ticket``...).
        _cost_itemtype: Cost itemtype.
        _foreign_key: Column of the child tables that holds the parent id (``tickets_id``...).
        _links: Link between ITIL objects by target kind (``tickets``, ``problems`` or ``changes``):
            ``(link itemtype, column with this parent id, column with the other object id)``.
    """

    # Search option ids of the actors (CommonITILObject::rawSearchOptions, GLPI 10)
    SEARCH_FIELD_REQUESTER = 4
    SEARCH_FIELD_ASSIGNED = 5
    SEARCH_FIELD_OBSERVER = 66
    SEARCH_FIELD_REQUESTER_GROUP = 71
    SEARCH_FIELD_ASSIGNED_GROUP = 8
    SEARCH_FIELD_OBSERVER_GROUP = 65

    _task_itemtype: ClassVar[str]
    _validation_itemtype: ClassVar[str | None] = None
    _actor_itemtypes: ClassVar[dict[ActorKind, str]]
    _item_link_itemtype: ClassVar[str]
    _cost_itemtype: ClassVar[str]
    _foreign_key: ClassVar[str]
    _links: ClassVar[dict[str, tuple[str, str, str]]]

    # --------------------------------------------------------------- helpers
    @classmethod
    def _child(cls, itemtype: str) -> type[CommonDBTM]:
        """Return the model of a child itemtype.

        Args:
            itemtype: Child itemtype.

        Returns:
            A ``CommonDBTM`` subclass bound to ``itemtype``.
        """
        return cls._for(itemtype)

    @classmethod
    def _polymorphic(cls, itil_id: int, data: dict[str, Any]) -> dict[str, Any]:
        """Bind a polymorphic child (``itemtype`` + ``items_id``) to the parent.

        Args:
            itil_id: Parent id.
            data: Child fields (not modified).

        Returns:
            A new dict where the parent binding wins over the caller values.
        """
        return {**data, "itemtype": cls._itemtype(), "items_id": itil_id}

    @classmethod
    def _owned(cls, itil_id: int, data: dict[str, Any]) -> dict[str, Any]:
        """Bind a child that has its own foreign key (``tickets_id``...) to the parent.

        Args:
            itil_id: Parent id.
            data: Child fields (not modified).

        Returns:
            A new dict where the parent binding wins over the caller values.
        """
        return {**data, cls._foreign_key: itil_id}

    @classmethod
    def _validation(cls) -> str:
        """Return the validation itemtype of the parent.

        Returns:
            The itemtype.

        Raises:
            UnsupportedOperationError: When the parent has no validations (Problem).
        """
        if cls._validation_itemtype is None:
            raise UnsupportedOperationError(f"{cls._itemtype()} has no validations")
        return cls._validation_itemtype

    # ------------------------------------------------------------ follow-ups
    @classmethod
    def add_followup(cls, itil_id: int, data: dict[str, Any]) -> int:
        """Add a follow-up.

        Args:
            itil_id: Parent id.
            data: Follow-up fields (``content``, ``is_private``, ``requesttypes_id``...); not modified.

        Returns:
            The follow-up id.
        """
        return cls._child("ITILFollowup").add(cls._polymorphic(itil_id, data))

    @classmethod
    def update_followup(cls, followup_id: int, data: dict[str, Any]) -> None:
        """Update a follow-up.

        Args:
            followup_id: Follow-up id.
            data: Fields to change; not modified.
        """
        cls._child("ITILFollowup").update(followup_id, data)

    @classmethod
    def delete_followup(cls, followup_id: int) -> None:
        """Delete a follow-up.

        Args:
            followup_id: Follow-up id.
        """
        cls._child("ITILFollowup").delete(followup_id)

    @classmethod
    def get_followups(cls, itil_id: int, **params: Any) -> list[dict[str, Any]]:
        """Return the follow-ups of the parent.

        Args:
            itil_id: Parent id.
            **params: Extra API parameters (``range``...).

        Returns:
            The follow-ups.
        """
        return cls.get_sub_items(itil_id, "ITILFollowup", **params)

    @classmethod
    def search_followups(cls, criteria: list[dict[str, Any]] | None = None, **params: Any) -> list[dict[str, Any]]:
        """Search follow-ups of any parent with the GLPI search engine.

        The search is not restricted to the parent itemtype: filter on the ``itemtype`` column
        (search option 6) when only the follow-ups of this kind are wanted.

        Args:
            criteria: Search criteria (``[{"field": 1, "searchtype": "contains", "value": "x"}]``).
            **params: Extra API parameters (``range``, ``sort``...).

        Returns:
            Search rows indexed by field id.
        """
        return cls._child("ITILFollowup").search(criteria, **params)

    # -------------------------------------------------------------- solutions
    @classmethod
    def add_solution(cls, itil_id: int, data: dict[str, Any]) -> int:
        """Add a solution.

        Args:
            itil_id: Parent id.
            data: Solution fields (``content``, ``solutiontypes_id``...); not modified.

        Returns:
            The solution id.
        """
        return cls._child("ITILSolution").add(cls._polymorphic(itil_id, data))

    @classmethod
    def update_solution(cls, solution_id: int, data: dict[str, Any]) -> None:
        """Update a solution.

        Args:
            solution_id: Solution id.
            data: Fields to change; not modified.
        """
        cls._child("ITILSolution").update(solution_id, data)

    @classmethod
    def delete_solution(cls, solution_id: int) -> None:
        """Delete a solution.

        Args:
            solution_id: Solution id.
        """
        cls._child("ITILSolution").delete(solution_id)

    @classmethod
    def get_solutions(cls, itil_id: int, **params: Any) -> list[dict[str, Any]]:
        """Return the solutions of the parent.

        Args:
            itil_id: Parent id.
            **params: Extra API parameters.

        Returns:
            The solutions.
        """
        return cls.get_sub_items(itil_id, "ITILSolution", **params)

    @classmethod
    def approve_solution(cls, itil_id: int, comment: str = "") -> int:
        """Approve the solution by adding a follow-up that carries ``add_close``.

        GLPI closes the parent only when it is solved (``ParentStatus``); on any other status the
        follow-up is recorded and the status is not changed. The status is not checked here.

        Args:
            itil_id: Parent id.
            comment: Optional text; GLPI writes "Solution approved" when empty or blank.

        Returns:
            The id of the follow-up that records the approval.
        """
        data: dict[str, Any] = {"add_close": 1}
        # An empty comment is not sent: GLPI fills in its own text
        if comment and comment.strip():
            data["content"] = comment
        return cls._child("ITILFollowup").add(cls._polymorphic(itil_id, data))

    @classmethod
    def refuse_solution(cls, itil_id: int, comment: str) -> int:
        """Refuse the solution: GLPI reopens the parent when a follow-up carries ``add_reopen``.

        Args:
            itil_id: Parent id.
            comment: Reason of the refusal (required).

        Returns:
            The id of the follow-up that records the refusal.

        Raises:
            ValueError: When ``comment`` is empty (checked before any request).
        """
        if not isinstance(comment, str) or not comment.strip():
            raise ValueError("a comment is required to refuse a solution")
        return cls._child("ITILFollowup").add(cls._polymorphic(itil_id, {"add_reopen": 1, "content": comment}))

    # ----------------------------------------------------------------- tasks
    @classmethod
    def add_task(cls, itil_id: int, data: dict[str, Any]) -> int:
        """Add a task.

        Args:
            itil_id: Parent id.
            data: Task fields (``content``, ``state``, ``users_id_tech``, ``actiontime``...); not modified.

        Returns:
            The task id.
        """
        return cls._child(cls._task_itemtype).add(cls._owned(itil_id, data))

    @classmethod
    def update_task(cls, task_id: int, data: dict[str, Any]) -> None:
        """Update a task.

        Args:
            task_id: Task id.
            data: Fields to change; not modified.
        """
        cls._child(cls._task_itemtype).update(task_id, data)

    @classmethod
    def delete_task(cls, task_id: int) -> None:
        """Delete a task.

        Args:
            task_id: Task id.
        """
        cls._child(cls._task_itemtype).delete(task_id)

    @classmethod
    def get_tasks(cls, itil_id: int, **params: Any) -> list[dict[str, Any]]:
        """Return the tasks of the parent.

        Args:
            itil_id: Parent id.
            **params: Extra API parameters.

        Returns:
            The tasks.
        """
        return cls.get_sub_items(itil_id, cls._task_itemtype, **params)

    # ----------------------------------------------------------- validations
    @classmethod
    def add_validation(cls, itil_id: int, data: dict[str, Any]) -> int:
        """Request a validation (Ticket and Change only).

        Args:
            itil_id: Parent id.
            data: Validation fields (``users_id_validate``, ``comment_submission``...); not modified.

        Returns:
            The validation id.

        Raises:
            UnsupportedOperationError: On a Problem.
        """
        return cls._child(cls._validation()).add(cls._owned(itil_id, data))

    @classmethod
    def update_validation(cls, validation_id: int, data: dict[str, Any]) -> None:
        """Update a validation (Ticket and Change only).

        Args:
            validation_id: Validation id.
            data: Fields to change (``status``, ``comment_validation``...); not modified.

        Raises:
            UnsupportedOperationError: On a Problem.
        """
        cls._child(cls._validation()).update(validation_id, data)

    @classmethod
    def delete_validation(cls, validation_id: int) -> None:
        """Delete a validation (Ticket and Change only).

        Args:
            validation_id: Validation id.

        Raises:
            UnsupportedOperationError: On a Problem.
        """
        cls._child(cls._validation()).delete(validation_id)

    @classmethod
    def get_validations(cls, itil_id: int, **params: Any) -> list[dict[str, Any]]:
        """Return the validations of the parent (Ticket and Change only).

        Args:
            itil_id: Parent id.
            **params: Extra API parameters.

        Returns:
            The validations.

        Raises:
            UnsupportedOperationError: On a Problem.
        """
        return cls.get_sub_items(itil_id, cls._validation(), **params)

    # ---------------------------------------------------------------- actors
    @classmethod
    def add_actor(cls, itil_id: int, kind: ActorKind, actor_id: int, actor_type: ActorType, *,
                  use_notification: bool = True, alternative_email: str | None = None) -> int:
        """Add a user, group or supplier as an actor.

        Args:
            itil_id: Parent id.
            kind: Kind of actor.
            actor_id: Id of the user, group or supplier.
            actor_type: Role of the actor (requester, assigned or observer).
            use_notification: Notify the actor (users and suppliers only).
            alternative_email: E-mail used instead of the one of the actor (users and suppliers only).

        Returns:
            The id of the actor link.

        Raises:
            ValueError: When ``kind`` or ``actor_type`` is invalid, or ``alternative_email`` is given for a group.
        """
        kind = ActorKind(kind)
        actor_type = ActorType(actor_type)
        data: dict[str, Any] = {cls._foreign_key: itil_id, _ACTOR_FIELDS[kind]: actor_id, "type": int(actor_type)}
        if kind is ActorKind.GROUP:
            # Group links have neither notification nor e-mail columns
            if alternative_email is not None:
                raise ValueError("alternative_email does not apply to groups")
        else:
            data["use_notification"] = int(bool(use_notification))
            if alternative_email is not None:
                data["alternative_email"] = alternative_email
        return cls._child(cls._actor_itemtypes[kind]).add(data)

    @classmethod
    def delete_actor(cls, link_id: int, kind: ActorKind) -> None:
        """Remove an actor link.

        Args:
            link_id: Id of the actor link (not the id of the user, group or supplier).
            kind: Kind of actor.

        Raises:
            ValueError: When ``kind`` is invalid.
        """
        cls._child(cls._actor_itemtypes[ActorKind(kind)]).delete(link_id)

    @classmethod
    def get_actors(cls, itil_id: int, **params: Any) -> list[dict[str, Any]]:
        """Return the users, groups and suppliers of the parent.

        Args:
            itil_id: Parent id.
            **params: Extra API parameters (applied to each of the three requests).

        Returns:
            The actor links, each one with the extra ``kind`` key (``user``, ``group`` or ``supplier``).
        """
        actors: list[dict[str, Any]] = []
        for kind in ActorKind:
            rows = cls.get_sub_items(itil_id, cls._actor_itemtypes[kind], **params)
            # Copies: the rows returned by the connector are never modified
            actors.extend({**row, "kind": kind.value} for row in rows)
        return actors

    # ----------------------------------------------------------------- items
    @classmethod
    def add_item(cls, itil_id: int, itemtype: str, items_id: int) -> int:
        """Link an asset to the parent.

        Args:
            itil_id: Parent id.
            itemtype: Itemtype of the asset (``Computer``...).
            items_id: Id of the asset.

        Returns:
            The id of the link.
        """
        return cls._child(cls._item_link_itemtype).add(
            {cls._foreign_key: itil_id, "itemtype": itemtype, "items_id": items_id})

    @classmethod
    def delete_item(cls, link_id: int) -> None:
        """Remove the link of an asset.

        Args:
            link_id: Id of the link (not the id of the asset).
        """
        cls._child(cls._item_link_itemtype).delete(link_id)

    @classmethod
    def get_items(cls, itil_id: int, **params: Any) -> list[dict[str, Any]]:
        """Return the asset links of the parent.

        Args:
            itil_id: Parent id.
            **params: Extra API parameters.

        Returns:
            The links.
        """
        return cls.get_sub_items(itil_id, cls._item_link_itemtype, **params)

    # ----------------------------------------------------------------- costs
    @classmethod
    def add_cost(cls, itil_id: int, data: dict[str, Any]) -> int:
        """Add a cost.

        Args:
            itil_id: Parent id.
            data: Cost fields (``name``, ``cost_time``, ``cost_fixed``...); not modified.

        Returns:
            The cost id.
        """
        return cls._child(cls._cost_itemtype).add(cls._owned(itil_id, data))

    @classmethod
    def update_cost(cls, cost_id: int, data: dict[str, Any]) -> None:
        """Update a cost.

        Args:
            cost_id: Cost id.
            data: Fields to change; not modified.
        """
        cls._child(cls._cost_itemtype).update(cost_id, data)

    @classmethod
    def delete_cost(cls, cost_id: int) -> None:
        """Delete a cost.

        Args:
            cost_id: Cost id.
        """
        cls._child(cls._cost_itemtype).delete(cost_id)

    @classmethod
    def get_costs(cls, itil_id: int, **params: Any) -> list[dict[str, Any]]:
        """Return the costs of the parent.

        Args:
            itil_id: Parent id.
            **params: Extra API parameters.

        Returns:
            The costs.
        """
        return cls.get_sub_items(itil_id, cls._cost_itemtype, **params)

    # ------------------------------------------------------------- documents
    @classmethod
    def add_document(cls, itil_id: int, documents_id: int) -> int:
        """Attach an existing document to the parent.

        Args:
            itil_id: Parent id.
            documents_id: Id of the document.

        Returns:
            The id of the ``Document_Item`` link.
        """
        return cls._child("Document_Item").add(cls._polymorphic(itil_id, {"documents_id": documents_id}))

    @classmethod
    def delete_document(cls, link_id: int) -> None:
        """Detach a document.

        Args:
            link_id: Id of the ``Document_Item`` link (not the id of the document).
        """
        cls._child("Document_Item").delete(link_id)

    @classmethod
    def get_documents(cls, itil_id: int, **params: Any) -> list[dict[str, Any]]:
        """Return the document links of the parent.

        Args:
            itil_id: Parent id.
            **params: Extra API parameters.

        Returns:
            The ``Document_Item`` links.
        """
        return cls.get_sub_items(itil_id, "Document_Item", **params)

    # ----------------------------------------------------------------- links
    @classmethod
    def _link_spec(cls, target: str) -> tuple[str, str, str]:
        """Return the link description between the parent and another ITIL kind.

        Args:
            target: ``tickets``, ``problems`` or ``changes``.

        Returns:
            ``(link itemtype, column with this parent id, column with the other id)``.

        Raises:
            UnsupportedOperationError: When the parent cannot be linked to that kind (e.g. Problem to Problem).
        """
        spec = cls._links.get(target)
        if spec is None:
            raise UnsupportedOperationError(f"{cls._itemtype()} cannot be linked to {target}")
        return spec

    @classmethod
    def _link(cls, itil_id: int, target: str, other_id: int, extra: dict[str, Any] | None = None) -> int:
        """Create a link to another ITIL object.

        Args:
            itil_id: Parent id.
            target: ``tickets``, ``problems`` or ``changes``.
            other_id: Id of the other object.
            extra: Extra fields of the link row.

        Returns:
            The id of the link.
        """
        link_itemtype, own_column, other_column = cls._link_spec(target)
        return cls._child(link_itemtype).add({**(extra or {}), own_column: itil_id, other_column: other_id})

    @classmethod
    def _get_links(cls, itil_id: int, target: str, **params: Any) -> list[dict[str, Any]]:
        """Return the links to another ITIL kind.

        ``Ticket_Ticket`` has no ``tickets_id`` column, so GLPI does not filter its sub-item
        listing by parent: it is read with an anchored text search per column (``^id$``) and
        checked again here. ``searchText`` cannot be overridden through ``params``.

        Args:
            itil_id: Parent id.
            target: ``tickets``, ``problems`` or ``changes``.
            **params: Extra API parameters.

        Returns:
            The link rows of the parent.
        """
        link_itemtype, own_column, other_column = cls._link_spec(target)
        if link_itemtype != "Ticket_Ticket":
            return cls.get_sub_items(itil_id, link_itemtype, **params)
        model = cls._child(link_itemtype)
        found: dict[int, dict[str, Any]] = {}
        for column in (own_column, other_column):
            # Anchors (^id$) make GLPI match the whole value; the exact test below stays as a guard
            query = {"range": "0-9999", **params, "searchText": {column: f"^{itil_id}$"}}
            for row in model.get_all(**query):
                if str(row.get(column)) == str(itil_id):
                    found[int(row["id"])] = row
        return [found[key] for key in sorted(found)]

    @classmethod
    def link_ticket(cls, itil_id: int, tickets_id: int, link: LinkType = LinkType.LINKED) -> int:
        """Link the parent to a ticket.

        Args:
            itil_id: Parent id.
            tickets_id: Id of the ticket.
            link: Kind of relation; only ``Ticket`` to ``Ticket`` links carry it.

        Returns:
            The id of the link row.

        Raises:
            ValueError: When ``link`` is invalid, or is not ``LINKED`` on a Change or a Problem.
        """
        link = LinkType(link)
        extra = None
        if cls._link_spec("tickets")[0] == "Ticket_Ticket":
            extra = {"link": int(link)}
        elif link is not LinkType.LINKED:
            raise ValueError(f"{cls._itemtype()} links to tickets have no relation type")
        return cls._link(itil_id, "tickets", tickets_id, extra)

    @classmethod
    def link_problem(cls, itil_id: int, problems_id: int) -> int:
        """Link the parent to a problem.

        Args:
            itil_id: Parent id.
            problems_id: Id of the problem.

        Returns:
            The id of the link row.

        Raises:
            UnsupportedOperationError: On a Problem.
        """
        return cls._link(itil_id, "problems", problems_id)

    @classmethod
    def link_change(cls, itil_id: int, changes_id: int) -> int:
        """Link the parent to a change.

        Args:
            itil_id: Parent id.
            changes_id: Id of the change.

        Returns:
            The id of the link row.

        Raises:
            UnsupportedOperationError: On a Change.
        """
        return cls._link(itil_id, "changes", changes_id)

    @classmethod
    def get_linked_tickets(cls, itil_id: int, **params: Any) -> list[dict[str, Any]]:
        """Return the links of the parent to tickets.

        Args:
            itil_id: Parent id.
            **params: Extra API parameters.

        Returns:
            The link rows.
        """
        return cls._get_links(itil_id, "tickets", **params)

    @classmethod
    def get_linked_problems(cls, itil_id: int, **params: Any) -> list[dict[str, Any]]:
        """Return the links of the parent to problems.

        Args:
            itil_id: Parent id.
            **params: Extra API parameters.

        Returns:
            The link rows.

        Raises:
            UnsupportedOperationError: On a Problem.
        """
        return cls._get_links(itil_id, "problems", **params)

    @classmethod
    def get_linked_changes(cls, itil_id: int, **params: Any) -> list[dict[str, Any]]:
        """Return the links of the parent to changes.

        Args:
            itil_id: Parent id.
            **params: Extra API parameters.

        Returns:
            The link rows.

        Raises:
            UnsupportedOperationError: On a Change.
        """
        return cls._get_links(itil_id, "changes", **params)

    @classmethod
    def unlink(cls, link_itemtype: str, link_id: int) -> None:
        """Remove a link row to another ITIL object.

        Args:
            link_itemtype: Itemtype of the row (``Ticket_Ticket``, ``Problem_Ticket``, ``Change_Ticket``
                or ``Change_Problem``) as returned with the link.
            link_id: Id of the link row.

        Raises:
            UnsupportedOperationError: When the parent has no such link itemtype.
        """
        if link_itemtype not in {spec[0] for spec in cls._links.values()}:
            raise UnsupportedOperationError(f"{cls._itemtype()} has no {link_itemtype} links")
        cls._child(link_itemtype).delete(link_id)

    # ---------------------------------------------------------- search by actor
    @classmethod
    def get_by_requester(cls, users_id: int, **params: Any) -> list[dict[str, Any]]:
        """Search the objects requested by a user.

        Args:
            users_id: User id.
            **params: Extra search parameters (``range``, ``sort``...).

        Returns:
            Search rows indexed by field id.
        """
        return cls._by_field(cls.SEARCH_FIELD_REQUESTER, users_id, **params)

    @classmethod
    def get_by_assigned(cls, users_id: int, **params: Any) -> list[dict[str, Any]]:
        """Search the objects assigned to a user.

        Args:
            users_id: User id.
            **params: Extra search parameters.

        Returns:
            Search rows indexed by field id.
        """
        return cls._by_field(cls.SEARCH_FIELD_ASSIGNED, users_id, **params)

    @classmethod
    def get_by_observer(cls, users_id: int, **params: Any) -> list[dict[str, Any]]:
        """Search the objects watched by a user.

        Args:
            users_id: User id.
            **params: Extra search parameters.

        Returns:
            Search rows indexed by field id.
        """
        return cls._by_field(cls.SEARCH_FIELD_OBSERVER, users_id, **params)

    @classmethod
    def get_by_group(cls, groups_id: int, actor_type: ActorType, **params: Any) -> list[dict[str, Any]]:
        """Search the objects of a group in a role.

        Args:
            groups_id: Group id.
            actor_type: Role of the group.
            **params: Extra search parameters.

        Returns:
            Search rows indexed by field id.

        Raises:
            ValueError: When ``actor_type`` is invalid (checked before any request).
        """
        fields = {
            ActorType.REQUESTER: cls.SEARCH_FIELD_REQUESTER_GROUP,
            ActorType.ASSIGNED: cls.SEARCH_FIELD_ASSIGNED_GROUP,
            ActorType.OBSERVER: cls.SEARCH_FIELD_OBSERVER_GROUP,
        }
        return cls._by_field(fields[ActorType(actor_type)], groups_id, **params)

    @classmethod
    def _by_field(cls, field: int, value: int, **params: Any) -> list[dict[str, Any]]:
        """Run an ``equals`` search on one field.

        Args:
            field: Search option id.
            value: Value to match.
            **params: Extra search parameters.

        Returns:
            Search rows indexed by field id.
        """
        return cls.search([{"field": field, "searchtype": "equals", "value": value}], **params)
