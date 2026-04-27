from glpi_api_hero.common_dbtm import CommonDBTM
from glpi_api_hero.api_communication import ApiCommunication

class Group(CommonDBTM):

    # Tipos de ator em chamados (actor type)
    REQUESTER = 1
    ASSIGNED  = 2
    OBSERVER  = 3

    @classmethod
    def getAllUsers(cls, group_id: int, **kwargs):
        """Retorna todos os usuários vinculados ao grupo.

        Args:
            group_id (int): ID do grupo no GLPI.
            **kwargs: Parâmetros extras repassados à chamada (ex: range).

        Returns:
            list: Lista de registros Group_User.
        """
        return cls.get_sub_items(group_id, 'Group_User', **kwargs)

    @classmethod
    def addUser(cls, group_id: int, user_id: int):
        """Adiciona um usuário ao grupo criando um vínculo Group_User.

        Args:
            group_id (int): ID do grupo no GLPI.
            user_id (int): ID do usuário no GLPI.

        Returns:
            list: Resultado da operação retornado pela API.
        """
        return ApiCommunication.glpi.add('Group_User', {
            'groups_id': group_id,
            'users_id': user_id,
        })

    @classmethod
    def deleteUser(cls, group_id: int, user_id: int):
        """Remove um usuário do grupo excluindo o vínculo Group_User.

        Localiza o registro Group_User pelo group_id e user_id antes de deletar.

        Args:
            group_id (int): ID do grupo no GLPI.
            user_id (int): ID do usuário no GLPI.

        Returns:
            list | None: Resultado da deleção ou None se o vínculo não for encontrado.
        """
        membros = cls.getAllUsers(group_id)
        if not membros:
            return None

        link_id = next(
            (m['id'] for m in membros if m.get('users_id') == user_id),
            None,
        )
        if link_id is None:
            return None

        return ApiCommunication.glpi.delete('Group_User', [{'id': link_id}])

    @classmethod
    def getAllTickets(cls, group_id: int, actor_type: int = ASSIGNED, **kwargs):
        """Retorna chamados associados ao grupo conforme o tipo de ator.

        Args:
            group_id (int): ID do grupo no GLPI.
            actor_type (int): Tipo de ator — Group.REQUESTER (1), Group.ASSIGNED (2)
                              ou Group.OBSERVER (3). Padrão: ASSIGNED.
            **kwargs: Parâmetros extras repassados à busca (ex: range, sort).

        Returns:
            list: Lista de chamados encontrados.
        """
        # Mapeamento actor_type → field ID de grupo na busca de Ticket
        field_map = {
            cls.REQUESTER: 71,  # "Requester group"
            cls.ASSIGNED:  8,   # "Assigned to - Group"
            cls.OBSERVER:  65,  # "Watcher group"
        }
        field_id = field_map.get(actor_type, 8)

        criteria = [
            {
                'field': field_id,
                'searchtype': 'equals',
                'value': group_id,
            }
        ]
        return ApiCommunication.glpi.search('Ticket', criteria=criteria, **kwargs)

    @classmethod
    def getByName(cls, name: str, **kwargs):
        """Busca um grupo pelo nome.

        Args:
            name (str): Nome do grupo no GLPI.
            **kwargs: Parâmetros extras repassados à busca.

        Returns:
            list: Lista de grupos encontrados.
        """
        criteria = [
            {
                'field': 1,
                'searchtype': 'equals',
                'value': name,
            }
        ]
        return ApiCommunication.glpi.search('Group', criteria=criteria, **kwargs)
