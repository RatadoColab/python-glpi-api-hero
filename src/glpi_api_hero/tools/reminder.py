"""Reminders (Tools > Reminders)."""

from __future__ import annotations

from typing import Any, ClassVar

from glpi_api_hero.core.capabilities import HasDocuments, HasLogs
from glpi_api_hero.tools._targets import collect_targets


class Reminder(HasDocuments, HasLogs):
    """GLPI ``Reminder``."""

    # Target relations of a reminder: kind -> (relation itemtype, column with the target id)
    _TARGETS: ClassVar[dict[str, tuple[str, str]]] = {
        "entity": ("Entity_Reminder", "entities_id"),
        "group": ("Group_Reminder", "groups_id"),
        "profile": ("Profile_Reminder", "profiles_id"),
        "user": ("Reminder_User", "users_id"),
    }

    @classmethod
    def get_targets(cls, reminder_id: int, **params: Any) -> list[dict[str, Any]]:
        """Return who can see the reminder (entities, groups, profiles and users).

        Args:
            reminder_id: Reminder id.
            **params: Extra API parameters (applied to each of the four requests).

        Returns:
            The relation rows with the extra keys ``kind`` and ``target_id``; ``[]`` without targets.
        """
        return collect_targets(cls, reminder_id, cls._TARGETS, **params)
