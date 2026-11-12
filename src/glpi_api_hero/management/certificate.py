"""Certificates (GLPI ``Certificate``)."""

from __future__ import annotations

from typing import Any

from glpi_api_hero.core.capabilities import (
    HasContracts,
    HasDocuments,
    HasDomains,
    HasInfocom,
    HasLogs,
    HasNotes,
    HasTickets,
)


class Certificate(HasInfocom, HasContracts, HasDocuments, HasDomains, HasTickets, HasNotes, HasLogs):
    """GLPI ``Certificate`` (Management > Certificates)."""

    @classmethod
    def get_items(cls, certificate_id: int, **params: Any) -> list[dict[str, Any]]:
        """Return the items using the certificate (``Certificate_Item``).

        Args:
            certificate_id: Id of the parent.
            **params: Extra API parameters.

        Returns:
            The rows.
        """
        return cls.get_sub_items(certificate_id, "Certificate_Item", **params)
