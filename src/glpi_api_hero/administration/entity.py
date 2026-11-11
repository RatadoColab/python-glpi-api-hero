"""Entities (Administration > Entities)."""

from __future__ import annotations

from glpi_api_hero.core.capabilities import HasDocuments, HasNotes
from glpi_api_hero.core.common_tree_dropdown import CommonTreeDropdown


class Entity(CommonTreeDropdown, HasDocuments, HasNotes):
    """GLPI ``Entity``."""
