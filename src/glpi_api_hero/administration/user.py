from typing import Any

from glpi_api_hero.assistance.ticket import Ticket
from glpi_api_hero.core.common_dbtm import CommonDBTM
from glpi_api_hero.core.constants import ActorType


class User(CommonDBTM):
    """GLPI users (Administration > Users)."""

    # Search option ids of the User itemtype (GLPI 10 rawSearchOptions)
    SEARCH_FIELD_LOGIN = 1
    SEARCH_FIELD_EMAIL = 5
    SEARCH_FIELD_LOCATION = 3

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
            ActorType.REQUESTER: Ticket.SEARCH_FIELD_REQUESTER,
            ActorType.ASSIGNED: Ticket.SEARCH_FIELD_ASSIGNED,
            ActorType.OBSERVER: Ticket.SEARCH_FIELD_OBSERVER,
        }
        field_id = field_map.get(actor_type, Ticket.SEARCH_FIELD_REQUESTER)

        criteria = [
            {
                "field": field_id,
                "searchtype": "equals",
                "value": user_id,
            }
        ]
        return Ticket.search(criteria, **kwargs)

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
                "field": cls.SEARCH_FIELD_LOGIN,  # campo "Login"
                "searchtype": "equals",
                "value": username,
            }
        ]
        return cls.search(criteria, **kwargs)

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
                "field": cls.SEARCH_FIELD_EMAIL,  # campo "Email"
                "searchtype": "equals",
                "value": email,
            }
        ]
        return cls.search(criteria, **kwargs)
