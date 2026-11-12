"""Suppliers (GLPI ``Supplier``)."""

from __future__ import annotations

from typing import Any

from glpi_api_hero.core.capabilities import HasDocuments, HasLogs, HasNotes


class Supplier(HasDocuments, HasNotes, HasLogs):
    """GLPI ``Supplier`` (Management > Suppliers)."""

    @classmethod
    def get_contacts(cls, supplier_id: int, **params: Any) -> list[dict[str, Any]]:
        """Return the contacts of the supplier (``Contact_Supplier``).

        Args:
            supplier_id: Id of the parent.
            **params: Extra API parameters.

        Returns:
            The rows.
        """
        return cls.get_sub_items(supplier_id, "Contact_Supplier", **params)

    @classmethod
    def get_contracts(cls, supplier_id: int, **params: Any) -> list[dict[str, Any]]:
        """Return the contracts of the supplier (``Contract_Supplier``).

        Args:
            supplier_id: Id of the parent.
            **params: Extra API parameters.

        Returns:
            The rows.
        """
        return cls.get_sub_items(supplier_id, "Contract_Supplier", **params)
