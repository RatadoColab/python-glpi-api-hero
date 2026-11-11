from typing import Any

from glpi_api_hero.assistance.ticket import Ticket
from glpi_api_hero.core.capabilities import HasCertificates, HasDocuments
from glpi_api_hero.core.common_dbtm import CommonDBTM
from glpi_api_hero.core.constants import ActorType


class User(HasDocuments, HasCertificates, CommonDBTM):
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
    def get_emails(cls, user_id: int, **params: Any) -> list[dict[str, Any]]:
        """Return the e-mail addresses of the user (``UserEmail``).

        Args:
            user_id: User id.
            **params: Extra API parameters.

        Returns:
            The rows.
        """
        return cls.get_sub_items(user_id, "UserEmail", **params)

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
        # Delegate to the actor search of the ITIL base; unknown roles keep the requester search
        if actor_type == ActorType.ASSIGNED:
            return Ticket.get_by_assigned(user_id, **kwargs)
        if actor_type == ActorType.OBSERVER:
            return Ticket.get_by_observer(user_id, **kwargs)
        return Ticket.get_by_requester(user_id, **kwargs)

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
