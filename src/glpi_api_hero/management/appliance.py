"""Appliances (GLPI ``Appliance``)."""

from __future__ import annotations

from typing import Any

from glpi_api_hero.core.capabilities import (
    HasCertificates,
    HasContracts,
    HasDocuments,
    HasDomains,
    HasInfocom,
    HasLogs,
    HasNotes,
    HasTickets,
)


class Appliance(HasInfocom, HasContracts, HasDocuments, HasCertificates, HasDomains, HasTickets, HasNotes, HasLogs):
    """GLPI ``Appliance`` (Management > Appliances)."""

    @classmethod
    def get_items(cls, appliance_id: int, **params: Any) -> list[dict[str, Any]]:
        """Return the items of the appliance (``Appliance_Item``).

        Args:
            appliance_id: Id of the parent.
            **params: Extra API parameters.

        Returns:
            The rows.
        """
        return cls.get_sub_items(appliance_id, "Appliance_Item", **params)
