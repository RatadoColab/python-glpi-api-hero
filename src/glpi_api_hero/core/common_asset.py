"""Base of the physical assets (Computer, Monitor...): lookups by name, serial and inventory number."""

from __future__ import annotations

from typing import Any, ClassVar

from glpi_api_hero.core.capabilities import HasLogs


class CommonAsset(HasLogs):
    """Shared behavior of the assets that have a name, a serial and an inventory number.

    Subclasses add the capability mixins GLPI allows for their itemtype, including ``HasNotes`` where GLPI sets
    ``$usenotepad`` (see :mod:`glpi_api_hero.core.capabilities`).
    """

    # Search option ids (GLPI 10 rawSearchOptions; ``Unmanaged`` overrides the serial ones)
    SEARCH_FIELD_NAME: ClassVar[int] = 1
    SEARCH_FIELD_SERIAL: ClassVar[int] = 5
    SEARCH_FIELD_INVENTORY_NUMBER: ClassVar[int] = 6
    SEARCH_FIELD_LOCATION: ClassVar[int] = 3

    @classmethod
    def _find(cls, field: int, searchtype: str, value: str, **params: Any) -> list[dict[str, Any]]:
        """Run a one-criterion search.

        Args:
            field: Search option id.
            searchtype: GLPI search type (``contains``, ``equals``...).
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
            **params: Extra search parameters (``range``, ``sort``...).

        Returns:
            Search rows indexed by field id.
        """
        return cls._find(cls.SEARCH_FIELD_NAME, "contains", name, **params)

    @classmethod
    def get_by_serial(cls, serial: str, **params: Any) -> list[dict[str, Any]]:
        """Search by serial number (exact).

        Args:
            serial: Serial number.
            **params: Extra search parameters.

        Returns:
            Search rows indexed by field id.
        """
        return cls._find(cls.SEARCH_FIELD_SERIAL, "equals", serial, **params)

    @classmethod
    def get_by_inventory_number(cls, otherserial: str, **params: Any) -> list[dict[str, Any]]:
        """Search by inventory number (``otherserial``, exact).

        Args:
            otherserial: Inventory number.
            **params: Extra search parameters.

        Returns:
            Search rows indexed by field id.
        """
        return cls._find(cls.SEARCH_FIELD_INVENTORY_NUMBER, "equals", otherserial, **params)
