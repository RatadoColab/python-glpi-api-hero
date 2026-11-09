from glpi_api_hero.common_dbtm import CommonDBTM
from glpi_api_hero.api_communication import ApiCommunication

class User(CommonDBTM):

    # Tipos de ator em chamados (actor type)
    REQUESTER = 1
    ASSIGNED  = 2
    OBSERVER  = 3

    @classmethod
    def getAllProfiles(cls, user_id: int, **kwargs):
        """Retorna todos os perfis vinculados ao usuário."""
        return cls.get_sub_items(user_id, 'Profile_User', **kwargs)

    @classmethod
    def getAllGroups(cls, user_id: int, **kwargs):
        """Retorna todos os grupos dos quais o usuário faz parte."""
        return cls.get_sub_items(user_id, 'Group_User', **kwargs)

    @classmethod
    def getAllTickets(cls, user_id: int, actor_type: int = REQUESTER, **kwargs):
        """Retorna chamados associados ao usuário conforme o tipo de ator.

        Args:
            user_id (int): ID do usuário no GLPI.
            actor_type (int): Tipo de ator — User.REQUESTER (1), User.ASSIGNED (2)
                              ou User.OBSERVER (3). Padrão: REQUESTER.
            **kwargs: Parâmetros extras repassados à busca (ex: range, sort).

        Returns:
            list: Lista de chamados encontrados.
        """
        # Mapeamento actor_type → field ID na busca do GLPI
        field_map = {
            cls.REQUESTER: 4,   # campo "Requester" na busca de Ticket
            cls.ASSIGNED:  5,   # campo "Assigned to"
            cls.OBSERVER:  66,  # campo "Observer"
        }
        field_id = field_map.get(actor_type, 4)

        criteria = [
            {
                'field': field_id,
                'searchtype': 'equals',
                'value': user_id,
            }
        ]
        return ApiCommunication.glpi.search('Ticket', criteria=criteria, **kwargs)

    @classmethod
    def getByUsername(cls, username: str, **kwargs):
        """Busca um usuário pelo login (name).

        Args:
            username (str): Login do usuário no GLPI.
            **kwargs: Parâmetros extras repassados à busca.

        Returns:
            list: Lista de usuários encontrados.
        """
        criteria = [
            {
                'field': 1,          # campo "Login"
                'searchtype': 'equals',
                'value': username,
            }
        ]
        return ApiCommunication.glpi.search('User', criteria=criteria, **kwargs)

    @classmethod
    def getByEmail(cls, email: str, **kwargs):
        """Busca um usuário pelo e-mail.

        Args:
            email (str): Endereço de e-mail do usuário.
            **kwargs: Parâmetros extras repassados à busca.

        Returns:
            list: Lista de usuários encontrados.
        """
        criteria = [
            {
                'field': 5,          # campo "Email"
                'searchtype': 'equals',
                'value': email,
            }
        ]
        return ApiCommunication.glpi.search('User', criteria=criteria, **kwargs)
