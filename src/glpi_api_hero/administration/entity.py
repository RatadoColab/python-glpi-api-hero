"""Entities (Administration > Entities)."""

from __future__ import annotations

from typing import Any

from glpi_api_hero.core.capabilities import HasDocuments, HasLogs, HasNotes
from glpi_api_hero.core.common_tree_dropdown import CommonTreeDropdown


class Entity(CommonTreeDropdown, HasDocuments, HasLogs, HasNotes):
    """GLPI ``Entity``."""

    @classmethod
    def get_children(cls, parent_id: int, **params: Any) -> list[dict[str, Any]]:
        """Return the direct sub-entities of an entity.

        Entity overrides the search options of the tree base (option 13 is the country), so the children are read
        with a text search on ``entities_id`` anchored to the whole value.

        Args:
            parent_id: Parent entity id.
            **params: Extra API parameters (``range``...).

        Returns:
            The entity rows (item fields, not search rows).
        """
        return cls.get_all(**{**params, "searchText": {"entities_id": f"^{parent_id}$"}})

    @classmethod
    def get_roots(cls, **params: Any) -> list[dict[str, Any]]:
        """Return the entities whose parent is the root entity (id 0).

        Args:
            **params: Extra API parameters.

        Returns:
            The entity rows (item fields, not search rows).
        """
        return cls.get_children(0, **params)
