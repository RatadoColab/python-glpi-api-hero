"""Lines (GLPI ``Line``)."""

from __future__ import annotations

from glpi_api_hero.core.capabilities import HasContracts, HasDocuments, HasInfocom, HasLogs, HasNotes, HasTickets


class Line(HasInfocom, HasContracts, HasDocuments, HasTickets, HasNotes, HasLogs):
    """GLPI ``Line`` (Management > Lines)."""
