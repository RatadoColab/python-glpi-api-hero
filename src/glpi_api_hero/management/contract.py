"""Contracts (GLPI ``Contract``)."""

from __future__ import annotations

from typing import Any

from glpi_api_hero.core.capabilities import HasDocuments, HasLogs, HasNotes


class Contract(HasDocuments, HasNotes, HasLogs):
    """GLPI ``Contract`` (Management > Contracts)."""

    @classmethod
    def get_items(cls, contract_id: int, **params: Any) -> list[dict[str, Any]]:
        """Return the items covered by the contract (``Contract_Item``).

        Args:
            contract_id: Id of the parent.
            **params: Extra API parameters.

        Returns:
            The rows.
        """
        return cls.get_sub_items(contract_id, "Contract_Item", **params)

    @classmethod
    def get_suppliers(cls, contract_id: int, **params: Any) -> list[dict[str, Any]]:
        """Return the suppliers of the contract (``Contract_Supplier``).

        Args:
            contract_id: Id of the parent.
            **params: Extra API parameters.

        Returns:
            The rows.
        """
        return cls.get_sub_items(contract_id, "Contract_Supplier", **params)

    @classmethod
    def get_costs(cls, contract_id: int, **params: Any) -> list[dict[str, Any]]:
        """Return the costs of the contract (``ContractCost``).

        Args:
            contract_id: Id of the parent.
            **params: Extra API parameters.

        Returns:
            The rows.
        """
        return cls.get_sub_items(contract_id, "ContractCost", **params)

    @classmethod
    def add_item(cls, contract_id: int, itemtype: str, items_id: int) -> int:
        """Attach an item to the contract (``Contract_Item``).

        Args:
            contract_id: Contract id.
            itemtype: Itemtype of the item (``Computer``...).
            items_id: Id of the item.

        Returns:
            The id of the link row.
        """
        return cls._for("Contract_Item").add({"contracts_id": contract_id, "itemtype": itemtype, "items_id": items_id})

    @classmethod
    def delete_item(cls, link_id: int) -> None:
        """Detach an item from the contract.

        Args:
            link_id: Id of the ``Contract_Item`` link row (not the id of the item).
        """
        cls._for("Contract_Item").delete(link_id)
