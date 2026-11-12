"""Contacts (GLPI ``Contact``)."""

from __future__ import annotations

from typing import Any

from glpi_api_hero.core.capabilities import HasDocuments, HasLogs, HasNotes


class Contact(HasDocuments, HasNotes, HasLogs):
    """GLPI ``Contact`` (Management > Contacts)."""

    @classmethod
    def get_suppliers(cls, contact_id: int, **params: Any) -> list[dict[str, Any]]:
        """Return the suppliers of the contact (``Contact_Supplier``).

        Args:
            contact_id: Id of the parent.
            **params: Extra API parameters.

        Returns:
            The rows.
        """
        return cls.get_sub_items(contact_id, "Contact_Supplier", **params)
