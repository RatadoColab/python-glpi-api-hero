"""Profiles (Administration > Profiles)."""

from __future__ import annotations

from typing import Any

from glpi_api_hero.core.common_dbtm import CommonDBTM


class Profile(CommonDBTM):
    """GLPI ``Profile``."""

    @classmethod
    def get_users(cls, profile_id: int, **params: Any) -> list[dict[str, Any]]:
        """Return the users that hold the profile (``Profile_User``).

        Args:
            profile_id: Parent id.
            **params: Extra API parameters.

        Returns:
            The rows.
        """
        return cls.get_sub_items(profile_id, "Profile_User", **params)
