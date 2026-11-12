"""Knowledge base (Tools > Knowledge base)."""

from __future__ import annotations

from typing import Any, ClassVar

from glpi_api_hero.core.capabilities import HasDocuments, HasLogs
from glpi_api_hero.tools._targets import collect_targets


class KnowbaseItem(HasDocuments, HasLogs):
    """GLPI ``KnowbaseItem``."""

    # Target relations of an article: kind -> (relation itemtype, column with the target id)
    _TARGETS: ClassVar[dict[str, tuple[str, str]]] = {
        "entity": ("Entity_KnowbaseItem", "entities_id"),
        "group": ("Group_KnowbaseItem", "groups_id"),
        "profile": ("KnowbaseItem_Profile", "profiles_id"),
        "user": ("KnowbaseItem_User", "users_id"),
    }

    @classmethod
    def get_items(cls, knowbaseitem_id: int, **params: Any) -> list[dict[str, Any]]:
        """Return the items linked to the article (``KnowbaseItem_Item``).

        Args:
            knowbaseitem_id: Parent id.
            **params: Extra API parameters.

        Returns:
            The rows.
        """
        return cls.get_sub_items(knowbaseitem_id, "KnowbaseItem_Item", **params)

    @classmethod
    def get_targets(cls, knowbaseitem_id: int, **params: Any) -> list[dict[str, Any]]:
        """Return who can see the article (entities, groups, profiles and users).

        Args:
            knowbaseitem_id: Reminder id.
            **params: Extra API parameters (applied to each of the four requests).

        Returns:
            The relation rows with the extra keys ``kind`` and ``target_id``; ``[]`` without targets.
        """
        return collect_targets(cls, knowbaseitem_id, cls._TARGETS, **params)
