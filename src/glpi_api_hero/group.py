from glpi_api_hero.common_dbtm import CommonDBTM

class Group(CommonDBTM):

    @classmethod
    def getAllUsers(cls, group_id: int):
        # Retornar todos os usuários de um grupo.
        pass

    @classmethod
    def addUser(cls, group_id: int, user_id: int):
        # Adicionar um usuário a um grupo.
        pass

    @classmethod
    def deleteUser(cls, group_id: int, user_id: int):
        # Excluir um usuário de um grupo.
        pass

    @classmethod
    def getAllTickets(cls, group_id: int, type: int, **kwargs):
        # Retornar todos os tickets de tum grupo de considerando os parâmetros enviados.
        pass
