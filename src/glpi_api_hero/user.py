from glpi_api_hero.common_dbtm import CommonDBTM

class User(CommonDBTM):

    @classmethod
    def getAllProfiles(cls, user_id: int):
        # Retornar todos os perfis de um usuário.
        pass

    @classmethod
    def getAllGroups(cls, user_id: int):
        # Retornar todos os grupos dos quais o usuário faz parte.
        pass

    @classmethod
    def getAllTickets(cls, user_id: int, type: int, **kwargs):
        # Retornar todos os tickets abertos por um usuário.
        pass


