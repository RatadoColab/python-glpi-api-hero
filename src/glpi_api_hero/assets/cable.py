"""Cables (GLPI ``Cable``)."""

from __future__ import annotations

from glpi_api_hero.core.capabilities import HasInfocom, HasLogs, HasTickets


class Cable(HasInfocom, HasTickets, HasLogs):
    """GLPI ``Cable`` (Assets > Cables)."""
