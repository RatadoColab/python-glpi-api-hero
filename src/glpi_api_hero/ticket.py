from glpi_api_hero.common_dbtm import CommonDBTM
from glpi_api_hero.itilfollowup import ITILFollowUp
from glpi_api_hero.itilsolution import ITILSolution
from glpi_api_hero.ticket_validation import TicketValidation
from glpi_api_hero.task import Task
from glpi_api_hero.item import Item
from glpi_api_hero.actor import Actor
from glpi_api_hero.linked_ticket import LinkedTicket

class Ticket(CommonDBTM):
   
    # Métodos FollowUp ################################

    @classmethod
    def addFollowUp(cls, ticket_id: int, data: dict):
        data['items_id'] = ticket_id
        data['itemtype'] = cls.__name__
        
        return ITILFollowUp.add(data)

    @classmethod
    def updateFollowUp(cls, followup_id: int, data: dict):
        data['items_id'] = followup_id

        return ITILFollowUp.update(data)
    
    @classmethod
    def deleteFollowUp(cls, followup_id: int):
        
        return ITILFollowUp.delete(followup_id)

    @classmethod
    def getFollowUps(cls, ticket_id: int):
        
        return ITILFollowUp.get(ticket_id)

    @classmethod
    def searchFollowUps(cls, **kwargs):
        # Inserir o ticket_id como um kwarg
        
        return ITILFollowUp.search(kwargs)

    # Métodos Solution ################################
    
    @classmethod
    def addSolution(cls, ticket_id: int, data: dict):
        data['items_id'] = ticket_id
        data['itemtype'] = cls.__name__
    
        return ITILSolution.add(data)

    @classmethod
    def updateSolution(cls, solution_id: int, data: dict):
        data['items_id'] = solution_id

        return ITILSolution.update(data)

    @classmethod
    def deleteSolution(cls, solution_id: int):
        
        return ITILSolution.delete(solution_id)

    @classmethod
    def getSolution(cls, ticket_id: int):
        
        return ITILSolution.get(ticket_id)
    
    @classmethod
    def ApprovalSolution(cls, solution_id: int):
        
        return ITILSolution.add(solution_id)
    
    # Métodos Validation ################################
    
    @classmethod
    def addValidation(cls, ticket_id: int, data: dict):
        data['items_id'] = ticket_id
        data['itemtype'] = cls.__name__
    
        return TicketValidation.add(data)

    @classmethod
    def updateValidation(cls, validation_id: int, data:dict):
        data['items_id'] = validation_id

        return TicketValidation.update(data)

    @classmethod
    def deleteValidation(cls, validation_id: int):
        
        return TicketValidation.delete(validation_id)

    @classmethod
    def getValidations(cls, ticket_id: int, **kwargs):
        
        return TicketValidation.get(ticket_id)
    
    # Métodos Task ################################
    
    @classmethod
    def addTask(cls, ticket_id: int, data: dict):
        data['items_id'] = ticket_id
        data['itemtype'] = cls.__name__
    
        return Task.add(data)

    @classmethod
    def updateTask(cls, validation_id: int, data:dict):
        data['items_id'] = validation_id

        return Task.update(data)

    @classmethod
    def deleteTask(cls, validation_id: int):
        
        return Task.delete(validation_id)

    @classmethod
    def getTasks(cls, ticket_id: int, **kwargs):
        
        return Task.get(ticket_id)
       
    # Métodos Item ################################
    
    @classmethod
    def addItem(cls, ticket_id: int, data: dict):
        data['items_id'] = ticket_id
        data['itemtype'] = cls.__name__
    
        return Item.add(data)

    @classmethod
    def deleteItem(cls, item_id: int):
        
        return Item.delete(item_id)

    @classmethod
    def getItems(cls, ticket_id: int, **kwargs):
        
        return Item.get(ticket_id)

    # Métodos Actors ################################
    
    @classmethod
    def addActor(cls, ticket_id: int, data: dict):
        data['items_id'] = ticket_id
        data['itemtype'] = cls.__name__
    
        return Actor.add(data)

    @classmethod
    def deleteActor(cls, actor_id: int):
        
        return Actor.delete(actor_id)

    @classmethod
    def getActors(cls, ticket_id: int, **kwargs):
        
        return Actor.get(ticket_id)
    
    # Métodos LinkedTickets ################################
    
    @classmethod
    def addLinkedTicket(cls, ticket_id: int, data: dict):
        data['items_id'] = ticket_id
        data['itemtype'] = cls.__name__
    
        return LinkedTicket.add(data)

    @classmethod
    def deleteLinkedTicket(cls, linked_ticket_id: int):
        
        return LinkedTicket.delete(linked_ticket_id)

    @classmethod
    def getLinkedTickets(cls, ticket_id: int, **kwargs):
        
        return LinkedTicket.get(ticket_id)
    
    #####################################################

    '''
    Adicionar métodos:
        Task: addTask, updateTask, deleteTask, getTasks.
        Solution: *ApprovalSolution
        Items: addItem, deleteItem, getItems
        Actors: addActor, deleteActor, getActors
        LinkedTickets: addLinkedTicket, deleteLinkedTicket, getLinkedTickets
    '''
