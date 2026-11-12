"""Database instances (GLPI ``DatabaseInstance``)."""

from __future__ import annotations

from typing import Any

from glpi_api_hero.core.capabilities import (
    HasAppliances,
    HasCertificates,
    HasContracts,
    HasDocuments,
    HasDomains,
    HasInfocom,
    HasLogs,
    HasNotes,
    HasTickets,
)


class DatabaseInstance(
    HasInfocom,
    HasContracts,
    HasDocuments,
    HasCertificates,
    HasDomains,
    HasAppliances,
    HasTickets,
    HasNotes,
    HasLogs,
):
    """GLPI ``DatabaseInstance`` (Management > Database instances)."""

    @classmethod
    def get_databases(cls, instance_id: int, **params: Any) -> list[dict[str, Any]]:
        """Return the databases of the instance (``Database``).

        Args:
            instance_id: Instance id.
            **params: Extra API parameters.

        Returns:
            The rows.
        """
        return cls.get_sub_items(instance_id, "Database", **params)

    @classmethod
    def add_database(cls, instance_id: int, data: dict[str, Any]) -> int:
        """Add a database to the instance.

        Args:
            instance_id: Instance id.
            data: Database fields (``name``...); not modified.

        Returns:
            The database id.
        """
        return cls._for("Database").add({**data, "databaseinstances_id": instance_id})

    @classmethod
    def update_database(cls, database_id: int, data: dict[str, Any]) -> None:
        """Update a database.

        Args:
            database_id: Database id.
            data: Fields to change; not modified.
        """
        cls._for("Database").update(database_id, data)

    @classmethod
    def delete_database(cls, database_id: int) -> None:
        """Delete a database.

        Args:
            database_id: Database id.
        """
        cls._for("Database").delete(database_id)
