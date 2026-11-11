"""Base of the hierarchical dropdowns (Location, ITILCategory, State, Entity, Group)."""

from __future__ import annotations

from typing import Any, ClassVar

from glpi_api_hero.core.common_dbtm import CommonDBTM


class CommonTreeDropdown(CommonDBTM):
    """Shared lookups of the tree-shaped itemtypes (``CommonTreeDropdown`` of GLPI 10)."""

    # Search option ids of CommonTreeDropdown::rawSearchOptions
    SEARCH_FIELD_COMPLETE_NAME: ClassVar[int] = 1
    SEARCH_FIELD_NAME: ClassVar[int] = 14
    SEARCH_FIELD_PARENT: ClassVar[int] = 13

    @classmethod
    def _find(cls, field: int, searchtype: str, value: Any, **params: Any) -> list[dict[str, Any]]:
        """Run a one-criterion search.

        Args:
            field: Search option id.
            searchtype: GLPI search type.
            value: Value to match.
            **params: Extra search parameters.

        Returns:
            Search rows indexed by field id.
        """
        return cls.search([{"field": field, "searchtype": searchtype, "value": value}], **params)

    @classmethod
    def get_by_name(cls, name: str, **params: Any) -> list[dict[str, Any]]:
        """Search by name (contains).

        Args:
            name: Text to find in the name.
            **params: Extra search parameters.

        Returns:
            Search rows indexed by field id.
        """
        return cls._find(cls.SEARCH_FIELD_NAME, "contains", name, **params)

    @classmethod
    def get_by_complete_name(cls, complete_name: str, **params: Any) -> list[dict[str, Any]]:
        """Search by complete name, the hierarchical path (contains).

        Args:
            complete_name: Path text (e.g. ``HQ > Building A``).
            **params: Extra search parameters.

        Returns:
            Search rows indexed by field id.
        """
        return cls._find(cls.SEARCH_FIELD_COMPLETE_NAME, "contains", complete_name, **params)

    @classmethod
    def get_children(cls, parent_id: int, **params: Any) -> list[dict[str, Any]]:
        """Search the direct children of one node.

        Args:
            parent_id: Parent id.
            **params: Extra search parameters.

        Returns:
            Search rows indexed by field id.
        """
        return cls._find(cls.SEARCH_FIELD_PARENT, "equals", parent_id, **params)

    @classmethod
    def get_roots(cls, **params: Any) -> list[dict[str, Any]]:
        """Search the nodes without a parent.

        Args:
            **params: Extra search parameters.

        Returns:
            Search rows indexed by field id.
        """
        return cls._find(cls.SEARCH_FIELD_PARENT, "equals", 0, **params)
