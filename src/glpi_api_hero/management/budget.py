"""Budgets (GLPI ``Budget``)."""

from __future__ import annotations

from glpi_api_hero.core.capabilities import HasDocuments, HasLogs, HasNotes


class Budget(HasDocuments, HasNotes, HasLogs):
    """GLPI ``Budget`` (Management > Budgets)."""
