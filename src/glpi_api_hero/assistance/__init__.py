"""Models of the Assistance menu."""

from glpi_api_hero.assistance.change import Change
from glpi_api_hero.assistance.problem import Problem
from glpi_api_hero.assistance.recurrent_change import RecurrentChange
from glpi_api_hero.assistance.ticket import Ticket
from glpi_api_hero.assistance.ticket_recurrent import TicketRecurrent

__all__ = ["Change", "Problem", "RecurrentChange", "Ticket", "TicketRecurrent"]
