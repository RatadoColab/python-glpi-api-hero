"""Software (GLPI ``Software``)."""

from __future__ import annotations

from typing import Any

from glpi_api_hero.core.capabilities import (
    HasAppliances,
    HasContracts,
    HasDocuments,
    HasDomains,
    HasInfocom,
    HasLogs,
    HasNotes,
    HasReservation,
    HasTickets,
)


class Software(
    HasInfocom,
    HasContracts,
    HasDocuments,
    HasDomains,
    HasAppliances,
    HasReservation,
    HasTickets,
    HasNotes,
    HasLogs,
):
    """GLPI ``Software`` (Assets > Software; not a physical asset)."""

    @classmethod
    def get_versions(cls, software_id: int, **params: Any) -> list[dict[str, Any]]:
        """Return the versions of the software (``SoftwareVersion``).

        Args:
            software_id: Software id.
            **params: Extra API parameters.

        Returns:
            The rows.
        """
        return cls.get_sub_items(software_id, "SoftwareVersion", **params)

    @classmethod
    def get_licenses(cls, software_id: int, **params: Any) -> list[dict[str, Any]]:
        """Return the licenses of the software (``SoftwareLicense``).

        Args:
            software_id: Software id.
            **params: Extra API parameters.

        Returns:
            The rows.
        """
        return cls.get_sub_items(software_id, "SoftwareLicense", **params)

    @classmethod
    def get_installations(cls, software_id: int, **params: Any) -> list[dict[str, Any]]:
        """Return where the software is installed (``Item_SoftwareVersion`` of every version).

        GLPI does not filter ``Item_SoftwareVersion`` by software, so each version is read on its own
        (one request for the versions plus one per version).

        Args:
            software_id: Software id.
            **params: Extra API parameters (applied to each request).

        Returns:
            The installation rows of all versions.
        """
        rows: list[dict[str, Any]] = []
        for version in cls.get_versions(software_id):
            rows.extend(cls._for("SoftwareVersion").get_sub_items(int(version["id"]), "Item_SoftwareVersion", **params))
        return rows
