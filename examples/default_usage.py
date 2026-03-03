from PythonGlpiApiHero.models.User import User
from PythonGlpiApiHero.models.Computer import Computer
from PythonGlpiApiHero.models.Ticket import Ticket
from PythonGlpiApiHero.models.ITILFollowUp import ITILFollowUp
from PythonGlpiApiHero.models.ITILSolution import ITILSolution
from PythonGlpiApiHero.models.Task import Task
from PythonGlpiApiHero.models.TicketValidation import TicketValidation

def main():

    user = User.add("Leonardo", "leo@email.com")

    computer = Computer.add("PC-01", "192.168.0.10", user.id)

    ticket = Ticket.add(
        "Erro no sistema",
        "Sistema não responde",
        user_id=1,
        status="OPEN"
    )

    Ticket.update(ticket.id, status="IN_PROGRESS")

    abertos = Ticket.search(status="OPEN")

    fu1 = Ticket.addFollowUp(ticket.id, "Usuário enviou print.")
    fu2 = Ticket.addFollowUp(ticket.id, "Equipe iniciou análise.")

    Ticket.updateFollowUp(ticket.id, fu1["id"], comment="Print validado.")

    todos = Ticket.searchFollowUps(ticket.id)

    Ticket.deleteFollowUp(ticket.id, fu2["id"])
