"""Domains (GLPI ``Domain``)."""

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


class Domain(HasInfocom, HasContracts, HasDocuments, HasCertificates, HasTickets, HasNotes, HasLogs):
    """GLPI ``Domain`` (Management > Domains)."""

    @classmethod
    def get_items(cls, domain_id: int, **params: Any) -> list[dict[str, Any]]:
        """Return the items linked to the domain (``Domain_Item``).

        Args:
            domain_id: Id of the parent.
            **params: Extra API parameters.

        Returns:
            The rows.
        """
        return cls.get_sub_items(domain_id, "Domain_Item", **params)

    @classmethod
    def get_records(cls, domain_id: int, **params: Any) -> list[dict[str, Any]]:
        """Return the records of the domain (``DomainRecord``).

        Args:
            domain_id: Domain id.
            **params: Extra API parameters.

        Returns:
            The rows.
        """
        return cls.get_sub_items(domain_id, "DomainRecord", **params)

    @classmethod
    def add_record(cls, domain_id: int, data: dict[str, Any]) -> int:
        """Add a record to the domain.

        Args:
            domain_id: Domain id.
            data: Record fields (``name``, ``type``, ``data``...); not modified.

        Returns:
            The record id.
        """
        return cls._for("DomainRecord").add({**data, "domains_id": domain_id})

    @classmethod
    def update_record(cls, record_id: int, data: dict[str, Any]) -> None:
        """Update a record.

        Args:
            record_id: Record id.
            data: Fields to change; not modified.
        """
        cls._for("DomainRecord").update(record_id, data)

    @classmethod
    def delete_record(cls, record_id: int) -> None:
        """Delete a record.

        Args:
            record_id: Record id.
        """
        cls._for("DomainRecord").delete(record_id)
