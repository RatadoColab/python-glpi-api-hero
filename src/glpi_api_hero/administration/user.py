from typing import Any

from glpi_api_hero.assistance.ticket import Ticket
from glpi_api_hero.core.capabilities import HasCertificates, HasDocuments, HasLogs
from glpi_api_hero.core.common_dbtm import CommonDBTM
from glpi_api_hero.core.constants import ActorType


class User(HasDocuments, HasCertificates, HasLogs, CommonDBTM):
    """GLPI users (Administration > Users)."""

    # Search option ids of the User itemtype (GLPI 10 rawSearchOptions)
    SEARCH_FIELD_LOGIN = 1
    SEARCH_FIELD_EMAIL = 5
    SEARCH_FIELD_LOCATION = 3

    @classmethod
    def get_profiles(cls, user_id: int, **kwargs: Any) -> list[dict[str, Any]]:
        """Return the profiles assigned to the user (``Profile_User``).

        Args:
            user_id: User id.
            **kwargs: Extra API parameters.

        Returns:
            The profile rows.
        """
        return cls.get_sub_items(user_id, "Profile_User", **kwargs)

    @classmethod
    def get_emails(cls, user_id: int, **params: Any) -> list[dict[str, Any]]:
        """Return the e-mail addresses of the user (``UserEmail``).

        Args:
            user_id: User id.
            **params: Extra API parameters.

        Returns:
            The rows.
        """
        return cls.get_sub_items(user_id, "UserEmail", **params)

    @classmethod
    def get_groups(cls, user_id: int, **kwargs: Any) -> list[dict[str, Any]]:
        """Return the group memberships of the user (``Group_User``).

        Args:
            user_id: User id.
            **kwargs: Extra API parameters.

        Returns:
            The group membership rows.
        """
        return cls.get_sub_items(user_id, "Group_User", **kwargs)

    @classmethod
    def get_tickets(
        cls, user_id: int, actor_type: ActorType = ActorType.REQUESTER, **kwargs: Any
    ) -> list[dict[str, Any]]:
        """Search the tickets of a user in a given role.

        Args:
            user_id: User id.
            actor_type: Role: ``ActorType.REQUESTER``, ``ActorType.ASSIGNED``
                              or ``ActorType.OBSERVER``. Default: requester.
            **kwargs: Extra search parameters (``range``, ``sort``...).

        Returns:
            Search rows of the tickets.

        Raises:
            ValueError: When ``actor_type`` is not an ``ActorType``.
        """
        # Delegate to the actor search of the ITIL base; unknown roles are refused
        if actor_type not in tuple(ActorType):
            raise ValueError(f"{actor_type!r} is not a valid ActorType")
        if actor_type == ActorType.ASSIGNED:
            return Ticket.get_by_assigned(user_id, **kwargs)
        if actor_type == ActorType.OBSERVER:
            return Ticket.get_by_observer(user_id, **kwargs)
        return Ticket.get_by_requester(user_id, **kwargs)

    @classmethod
    def get_by_username(cls, username: str, **kwargs: Any) -> list[dict[str, Any]]:
        """Search a user by login.

        Args:
            username: Login of the user.
            **kwargs: Extra search parameters.

        Returns:
            Search rows of the users.
        """
        criteria = [
            {
                # Login field; "equals" compares the item id on link fields, so the anchored text match is used
                "field": cls.SEARCH_FIELD_LOGIN,
                "searchtype": "contains",
                "value": f"^{username}$",
            }
        ]
        return cls.search(criteria, **kwargs)

    @classmethod
    def get_by_email(cls, email: str, **kwargs: Any) -> list[dict[str, Any]]:
        """Search a user by e-mail.

        Args:
            email: E-mail address.
            **kwargs: Extra search parameters.

        Returns:
            Search rows of the users.
        """
        criteria = [
            {
                # E-mail field; anchored text match for an exact lookup
                "field": cls.SEARCH_FIELD_EMAIL,
                "searchtype": "contains",
                "value": f"^{email}$",
            }
        ]
        return cls.search(criteria, **kwargs)
