from typing import Any

from glpi_api_hero.core.common_dbtm import CommonDBTM
from glpi_api_hero.core.constants import ActorType
from glpi_api_hero.core.session import Glpi


class User(CommonDBTM):
    """GLPI users (Administration > Users)."""

    @classmethod
    def get_profiles(cls, user_id: int, **kwargs: Any) -> list[dict[str, Any]]:
        """Retorna todos os perfis vinculados ao usuário."""
        return cls.get_sub_items(user_id, "Profile_User", **kwargs)

    @classmethod
    def get_groups(cls, user_id: int, **kwargs: Any) -> list[dict[str, Any]]:
        """Retorna todos os grupos dos quais o usuário faz parte."""
        return cls.get_sub_items(user_id, "Group_User", **kwargs)

    @classmethod
    def get_tickets(
        cls, user_id: int, actor_type: ActorType = ActorType.REQUESTER, **kwargs: Any
    ) -> list[dict[str, Any]]:
        """Retorna chamados associados ao usuário conforme o tipo de ator.

        Args:
            user_id (int): ID do usuário no GLPI.
            actor_type (int): Tipo de ator — ActorType.REQUESTER (1), ActorType.ASSIGNED (2)
                              ou ActorType.OBSERVER (3). Padrão: REQUESTER.
            **kwargs: Parâmetros extras repassados à busca (ex: range, sort).

        Returns:
            list: Lista de chamados encontrados.
        """
        # Mapeamento actor_type → field ID na busca do GLPI
        field_map = {
            ActorType.REQUESTER: 4,  # campo "Requester" na busca de Ticket
            ActorType.ASSIGNED: 5,  # campo "Assigned to"
            ActorType.OBSERVER: 66,  # campo "Observer"
        }
        field_id = field_map.get(actor_type, 4)

        criteria = [
            {
                "field": field_id,
                "searchtype": "equals",
                "value": user_id,
            }
        ]
        return Glpi.connector().search("Ticket", criteria, **kwargs)

    @classmethod
    def get_by_username(cls, username: str, **kwargs: Any) -> list[dict[str, Any]]:
        """Busca um usuário pelo login (name).

        Args:
            username (str): Login do usuário no GLPI.
            **kwargs: Parâmetros extras repassados à busca.

        Returns:
            list: Lista de usuários encontrados.
        """
        criteria = [
            {
                "field": 1,  # campo "Login"
                "searchtype": "equals",
                "value": username,
            }
        ]
        return Glpi.connector().search("User", criteria, **kwargs)

    @classmethod
    def get_by_email(cls, email: str, **kwargs: Any) -> list[dict[str, Any]]:
        """Busca um usuário pelo e-mail.

        Args:
            email (str): Endereço de e-mail do usuário.
            **kwargs: Parâmetros extras repassados à busca.

        Returns:
            list: Lista de usuários encontrados.
        """
        criteria = [
            {
                "field": 5,  # campo "Email"
                "searchtype": "equals",
                "value": email,
            }
        ]
        return Glpi.connector().search("User", criteria, **kwargs)
