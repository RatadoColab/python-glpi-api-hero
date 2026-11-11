from typing import Any

from glpi_api_hero.assistance.ticket import Ticket
from glpi_api_hero.core.capabilities import HasLogs, HasNotes
from glpi_api_hero.core.common_dbtm import CommonDBTM
from glpi_api_hero.core.common_tree_dropdown import CommonTreeDropdown
from glpi_api_hero.core.constants import ActorType


class Group(CommonTreeDropdown, HasNotes, HasLogs):
    """GLPI groups (Administration > Groups)."""

    # Search option ids of the Group itemtype (GLPI 10 rawSearchOptions)
    SEARCH_FIELD_COMPLETE_NAME = 1
    SEARCH_FIELD_NAME = 14

    @classmethod
    def get_users(cls, group_id: int, **kwargs: Any) -> list[dict[str, Any]]:
        """Return the members of the group (``Group_User``).

        Args:
            group_id: Group id.
            **kwargs: Extra API parameters (``range``...).

        Returns:
            The ``Group_User`` rows.
        """
        return cls.get_sub_items(group_id, "Group_User", **kwargs)

    @classmethod
    def add_user(cls, group_id: int, user_id: int) -> int:
        """Add a user to the group (creates a ``Group_User`` link).

        Args:
            group_id: Group id.
            user_id: User id.

        Returns:
            The id of the new link.
        """
        return CommonDBTM._for("Group_User").add(
            {
                "groups_id": group_id,
                "users_id": user_id,
            }
        )

    @classmethod
    def delete_user(cls, group_id: int, user_id: int) -> None:
        """Remove a user from the group (deletes the ``Group_User`` link).

        The ``Group_User`` row is looked up by group and user before it is deleted.

        Args:
            group_id: Group id.
            user_id: User id.

        Returns:
            ``None`` always (also when the user was not a member).
        """
        # The whole membership is read: the default page would hide members beyond it
        members = cls.get_users(group_id, range="0-9999")
        if not members:
            return None

        link_id = next(
            (m["id"] for m in members if m.get("users_id") == user_id),
            None,
        )
        if link_id is None:
            return None

        return CommonDBTM._for("Group_User").delete(link_id)

    @classmethod
    def get_tickets(
        cls, group_id: int, actor_type: ActorType = ActorType.ASSIGNED, **kwargs: Any
    ) -> list[dict[str, Any]]:
        """Search the tickets of a group in a given role.

        Args:
            group_id: Group id.
            actor_type: Role: ``ActorType.REQUESTER``, ``ActorType.ASSIGNED``
                              or ``ActorType.OBSERVER``. Default: assigned.
            **kwargs: Extra search parameters (``range``, ``sort``...).

        Returns:
            Search rows of the tickets.
        """
        # Delegate to the actor search of the ITIL base; unknown roles keep the assigned-group search
        if actor_type not in tuple(ActorType):
            actor_type = ActorType.ASSIGNED
        return Ticket.get_by_group(group_id, actor_type, **kwargs)

    @classmethod
    def get_by_name(cls, name: str, **kwargs: Any) -> list[dict[str, Any]]:
        """Search a group by name.

        Args:
            name: Name of the group.
            **kwargs: Extra search parameters.

        Returns:
            Search rows of the groups.
        """
        criteria = [
            {
                "field": cls.SEARCH_FIELD_NAME,
                "searchtype": "equals",
                "value": name,
            }
        ]
        return cls.search(criteria, **kwargs)
