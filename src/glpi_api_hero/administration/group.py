from typing import Any

from glpi_api_hero.core.common_dbtm import CommonDBTM
from glpi_api_hero.core.constants import ActorType
from glpi_api_hero.core.session import Glpi


class Group(CommonDBTM):
    """GLPI groups (Administration > Groups)."""

    @classmethod
    def get_users(cls, group_id: int, **kwargs: Any) -> list[dict[str, Any]]:
        """Retorna todos os usuários vinculados ao grupo.

        Args:
            group_id (int): ID do grupo no GLPI.
            **kwargs: Parâmetros extras repassados à chamada (ex: range).

        Returns:
            list: Lista de registros Group_User.
        """
        return cls.get_sub_items(group_id, "Group_User", **kwargs)

    @classmethod
    def add_user(cls, group_id: int, user_id: int) -> int:
        """Adiciona um usuário ao grupo criando um vínculo Group_User.

        Args:
            group_id (int): ID do grupo no GLPI.
            user_id (int): ID do usuário no GLPI.

        Returns:
            list: Resultado da operação retornado pela API.
        """
        return CommonDBTM._for("Group_User").add(
            {
                "groups_id": group_id,
                "users_id": user_id,
            }
        )

    @classmethod
    def delete_user(cls, group_id: int, user_id: int) -> None:
        """Remove um usuário do grupo excluindo o vínculo Group_User.

        Localiza o registro Group_User pelo group_id e user_id antes de deletar.

        Args:
            group_id (int): ID do grupo no GLPI.
            user_id (int): ID do usuário no GLPI.

        Returns:
            list | None: Resultado da deleção ou None se o vínculo não for encontrado.
        """
        membros = cls.get_users(group_id)
        if not membros:
            return None

        link_id = next(
            (m["id"] for m in membros if m.get("users_id") == user_id),
            None,
        )
        if link_id is None:
            return None

        return CommonDBTM._for("Group_User").delete(link_id)

    @classmethod
    def get_tickets(
        cls, group_id: int, actor_type: ActorType = ActorType.ASSIGNED, **kwargs: Any
    ) -> list[dict[str, Any]]:
        """Retorna chamados associados ao grupo conforme o tipo de ator.

        Args:
            group_id (int): ID do grupo no GLPI.
            actor_type (int): Tipo de ator — ActorType.REQUESTER (1), ActorType.ASSIGNED (2)
                              ou ActorType.OBSERVER (3). Padrão: ASSIGNED.
            **kwargs: Parâmetros extras repassados à busca (ex: range, sort).

        Returns:
            list: Lista de chamados encontrados.
        """
        # Mapeamento actor_type → field ID de grupo na busca de Ticket
        field_map = {
            ActorType.REQUESTER: 71,  # "Requester group"
            ActorType.ASSIGNED: 8,  # "Assigned to - Group"
            ActorType.OBSERVER: 65,  # "Watcher group"
        }
        field_id = field_map.get(actor_type, 8)

        criteria = [
            {
                "field": field_id,
                "searchtype": "equals",
                "value": group_id,
            }
        ]
        return Glpi.connector().search("Ticket", criteria, **kwargs)

    @classmethod
    def get_by_name(cls, name: str, **kwargs: Any) -> list[dict[str, Any]]:
        """Busca um grupo pelo nome.

        Args:
            name (str): Nome do grupo no GLPI.
            **kwargs: Parâmetros extras repassados à busca.

        Returns:
            list: Lista de grupos encontrados.
        """
        criteria = [
            {
                "field": 1,
                "searchtype": "equals",
                "value": name,
            }
        ]
        return Glpi.connector().search("Group", criteria, **kwargs)
