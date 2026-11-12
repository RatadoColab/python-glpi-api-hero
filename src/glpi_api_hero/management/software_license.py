"""Licenses (GLPI ``SoftwareLicense``)."""

from __future__ import annotations

from typing import Any

from glpi_api_hero.core.capabilities import (
    HasCertificates,
    HasContracts,
    HasDocuments,
    HasInfocom,
    HasLogs,
    HasNotes,
    HasTickets,
)


class SoftwareLicense(HasInfocom, HasContracts, HasDocuments, HasCertificates, HasTickets, HasNotes, HasLogs):
    """GLPI ``SoftwareLicense`` (Management > Licenses)."""

    @classmethod
    def get_installations(cls, license_id: int, **params: Any) -> list[dict[str, Any]]:
        """Return where the license is used (``Item_SoftwareLicense``).

        Args:
            license_id: Id of the parent.
            **params: Extra API parameters.

        Returns:
            The rows.
        """
        return cls.get_sub_items(license_id, "Item_SoftwareLicense", **params)
