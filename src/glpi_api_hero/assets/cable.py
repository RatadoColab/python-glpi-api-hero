"""Cables (GLPI ``Cable``)."""

from __future__ import annotations

from glpi_api_hero.core.capabilities import HasInfocom, HasLogs, HasNotes, HasTickets


class Cable(HasInfocom, HasTickets, HasNotes, HasLogs):
    """GLPI ``Cable`` (Assets > Cables)."""
