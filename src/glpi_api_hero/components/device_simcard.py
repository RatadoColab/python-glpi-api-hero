"""SIM card component model (Components > Simcards)."""

from __future__ import annotations

from typing import Any

from glpi_api_hero.core.common_dbtm import CommonDBTM


class DeviceSimcard(CommonDBTM):
    """GLPI ``DeviceSimcard``: the SIM card model; installed cards are ``Item_DeviceSimcard`` rows."""

    @classmethod
    def get_installations(cls, devicesimcard_id: int, **params: Any) -> list[dict[str, Any]]:
        """Return where the SIM card model is installed (``Item_DeviceSimcard``).

        Args:
            devicesimcard_id: SIM card model id.
            **params: Extra API parameters.

        Returns:
            The rows.
        """
        return cls.get_sub_items(devicesimcard_id, "Item_DeviceSimcard", **params)
