from glpi_api_hero.common_dbtm import CommonDBTM
from glpi_api_hero.itilfollowup import ITILFollowUp
import glpi_api_hero.api_communication

class Ticket(CommonDBTM):
   
    # Métodos FollowUp

    @classmethod
    def addFollowUp(cls, ticket_id: int, data: dict):
        data['items_id'] = ticket_id;
        data['itemtype'] = cls.__name__;
        
        return ITILFollowUp.add(data);
        

    @classmethod
    def updateFollowUp(cls, followup_id: int):
        pass

    @classmethod
    def deleteFollowUp(cls, followup_id: int):
        pass

    @classmethod
    def getAllFollowUps(cls, ticket_id: int):
        pass

    @classmethod
    def searchFollowUps(cls, ticket_id: int, **kwargs):
        # Inserir o ticket_id como um kwarg
        
        return ITILFollowUp.search(kwargs)

    @classmethod
    def addITILSolution(cls, ticket_id: int, data: dict)):
        pass
    
    # Fazer o restante para ITILSolution
    
    def addDocument(cls, document):
        pass