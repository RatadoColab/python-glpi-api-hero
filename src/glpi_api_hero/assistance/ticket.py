from typing import Any

from glpi_api_hero.core._legacy_children import (
    Actor,
    Item,
    ITILFollowup,
    ITILSolution,
    LinkedTicket,
    Task,
    TicketValidation,
)
from glpi_api_hero.core.common_dbtm import CommonDBTM


class Ticket(CommonDBTM):
    """Tickets (Assistance > Tickets) with their provisional sub-item methods."""

    # Métodos FollowUp ################################

    @classmethod
    def add_followup(cls, ticket_id: int, data: dict[str, Any]) -> int:
        """Adiciona um acompanhamento (follow-up) a um chamado existente.

        Args:
            ticket_id (int): ID do chamado no GLPI.
            data (dict): Dados do acompanhamento. Campos comuns:
                - content (str): Texto do acompanhamento. Obrigatório.
                - is_private (int): 1 para privado, 0 para público. Padrão: 0.
                - requesttypes_id (int): ID do tipo de solicitação (telefone, e-mail, etc.).

        Returns:
            list: Resultado da operação contendo o ID do acompanhamento criado.
        """
        data["items_id"] = ticket_id
        data["itemtype"] = cls.__name__

        return ITILFollowup.add(data)

    @classmethod
    def update_followup(cls, followup_id: int, data: dict[str, Any]) -> None:
        """Atualiza um acompanhamento existente.

        Args:
            followup_id (int): ID do acompanhamento a ser atualizado.
            data (dict): Campos a atualizar. Campos comuns:
                - content (str): Novo texto do acompanhamento.
                - is_private (int): 1 para privado, 0 para público.

        Returns:
            list: Resultado da operação retornado pela API.
        """
        data["id"] = followup_id

        return ITILFollowup.update(followup_id, data)

    @classmethod
    def delete_followup(cls, followup_id: int) -> None:
        """Remove um acompanhamento de um chamado.

        Args:
            followup_id (int): ID do acompanhamento a ser removido.

        Returns:
            list: Resultado da operação retornado pela API.
        """
        return ITILFollowup.delete(followup_id)

    @classmethod
    def get_followups(cls, ticket_id: int) -> list[dict[str, Any]]:
        """Retorna todos os acompanhamentos de um chamado.

        Args:
            ticket_id (int): ID do chamado no GLPI.

        Returns:
            list: Lista de acompanhamentos do chamado.
        """
        return cls.get_sub_items(ticket_id, "ITILFollowup")

    @classmethod
    def search_followups(cls, **kwargs: Any) -> list[dict[str, Any]]:
        """Busca acompanhamentos com critérios variados.

        Args:
            **kwargs: Parâmetros de busca repassados à API (ex: criteria, range, sort).

        Returns:
            list: Lista de acompanhamentos encontrados.
        """
        return ITILFollowup.search(kwargs)

    # Métodos Solution ################################

    @classmethod
    def add_solution(cls, ticket_id: int, data: dict[str, Any]) -> int:
        """Adiciona uma solução a um chamado existente.

        Args:
            ticket_id (int): ID do chamado no GLPI.
            data (dict): Dados da solução. Campos comuns:
                - content (str): Texto da solução. Obrigatório.
                - solutiontypes_id (int): ID do tipo de solução.

        Returns:
            list: Resultado da operação contendo o ID da solução criada.
        """
        data["items_id"] = ticket_id
        data["itemtype"] = cls.__name__

        return ITILSolution.add(data)

    @classmethod
    def update_solution(cls, solution_id: int, data: dict[str, Any]) -> None:
        """Atualiza uma solução existente.

        Args:
            solution_id (int): ID da solução a ser atualizada.
            data (dict): Campos a atualizar. Campos comuns:
                - content (str): Novo texto da solução.
                - solutiontypes_id (int): Novo tipo de solução.

        Returns:
            list: Resultado da operação retornado pela API.
        """
        data["id"] = solution_id

        return ITILSolution.update(solution_id, data)

    @classmethod
    def delete_solution(cls, solution_id: int) -> None:
        """Remove uma solução de um chamado.

        Args:
            solution_id (int): ID da solução a ser removida.

        Returns:
            list: Resultado da operação retornado pela API.
        """
        return ITILSolution.delete(solution_id)

    @classmethod
    def get_solutions(cls, ticket_id: int) -> list[dict[str, Any]]:
        """Retorna todas as soluções de um chamado.

        Args:
            ticket_id (int): ID do chamado no GLPI.

        Returns:
            list: Lista de soluções do chamado.
        """
        return cls.get_sub_items(ticket_id, "ITILSolution")

    @classmethod
    def approve_solution(cls, solution_id: int) -> int:
        """Registra a aprovação de uma solução existente.

        Args:
            solution_id (int): ID da solução a ser aprovada.

        Returns:
            list: Resultado da operação retornado pela API.
        """
        return ITILSolution.add(solution_id)

    # Métodos Validation ################################

    @classmethod
    def add_validation(cls, ticket_id: int, data: dict[str, Any]) -> int:
        """Solicita validação de um chamado a um usuário aprovador.

        Args:
            ticket_id (int): ID do chamado no GLPI.
            data (dict): Dados da validação. Campos comuns:
                - users_id_validate (int): ID do usuário que deve validar. Obrigatório.
                - comment_submission (str): Comentário enviado ao aprovador.

        Returns:
            list: Resultado da operação contendo o ID da validação criada.
        """
        data["items_id"] = ticket_id
        data["itemtype"] = cls.__name__

        return TicketValidation.add(data)

    @classmethod
    def update_validation(cls, validation_id: int, data: dict[str, Any]) -> None:
        """Atualiza uma solicitação de validação existente.

        Args:
            validation_id (int): ID da validação a ser atualizada.
            data (dict): Campos a atualizar. Campos comuns:
                - status (int): Novo status — 2=Aceito, 4=Recusado.
                - comment_validation (str): Comentário do aprovador.

        Returns:
            list: Resultado da operação retornado pela API.
        """
        data["id"] = validation_id

        return TicketValidation.update(validation_id, data)

    @classmethod
    def delete_validation(cls, validation_id: int) -> None:
        """Remove uma solicitação de validação de um chamado.

        Args:
            validation_id (int): ID da validação a ser removida.

        Returns:
            list: Resultado da operação retornado pela API.
        """
        return TicketValidation.delete(validation_id)

    @classmethod
    def get_validations(cls, ticket_id: int, **kwargs: Any) -> list[dict[str, Any]]:
        """Retorna todas as validações de um chamado.

        Args:
            ticket_id (int): ID do chamado no GLPI.
            **kwargs: Parâmetros extras repassados à chamada.

        Returns:
            list: Lista de validações do chamado.
        """
        return cls.get_sub_items(ticket_id, "TicketValidation", **kwargs)

    # Métodos Task ################################

    @classmethod
    def add_task(cls, ticket_id: int, data: dict[str, Any]) -> int:
        """Adiciona uma tarefa a um chamado existente.

        Args:
            ticket_id (int): ID do chamado no GLPI.
            data (dict): Dados da tarefa. Campos comuns:
                - content (str): Descrição da tarefa. Obrigatório.
                - taskcategories_id (int): ID da categoria da tarefa.
                - state (int): Estado — 0=Informação, 1=A fazer, 2=Feito.
                - users_id_tech (int): ID do técnico responsável.
                - actiontime (int): Tempo previsto em segundos.

        Returns:
            list: Resultado da operação contendo o ID da tarefa criada.
        """
        data["items_id"] = ticket_id
        data["itemtype"] = cls.__name__

        return Task.add(data)

    @classmethod
    def update_task(cls, task_id: int, data: dict[str, Any]) -> None:
        """Atualiza uma tarefa existente em um chamado.

        Args:
            task_id (int): ID da tarefa a ser atualizada.
            data (dict): Campos a atualizar. Campos comuns:
                - content (str): Nova descrição da tarefa.
                - state (int): Novo estado — 0=Informação, 1=A fazer, 2=Feito.
                - actiontime (int): Tempo real gasto em segundos.

        Returns:
            list: Resultado da operação retornado pela API.
        """
        data["id"] = task_id

        return Task.update(task_id, data)

    @classmethod
    def delete_task(cls, task_id: int) -> None:
        """Remove uma tarefa de um chamado.

        Args:
            task_id (int): ID da tarefa a ser removida.

        Returns:
            list: Resultado da operação retornado pela API.
        """
        return Task.delete(task_id)

    @classmethod
    def get_tasks(cls, ticket_id: int, **kwargs: Any) -> list[dict[str, Any]]:
        """Retorna todas as tarefas de um chamado.

        Args:
            ticket_id (int): ID do chamado no GLPI.
            **kwargs: Parâmetros extras repassados à chamada.

        Returns:
            list: Lista de tarefas do chamado.
        """
        return cls.get_sub_items(ticket_id, "TicketTask", **kwargs)

    # Métodos Item ################################

    @classmethod
    def add_item(cls, ticket_id: int, data: dict[str, Any]) -> int:
        """Vincula um ativo (item) a um chamado existente.

        Args:
            ticket_id (int): ID do chamado no GLPI.
            data (dict): Dados do vínculo. Campos obrigatórios:
                - itemtype (str): Tipo do ativo (ex: 'Computer', 'Monitor').
                - items_id (int): ID do ativo no GLPI.

        Returns:
            list: Resultado da operação contendo o ID do vínculo criado.
        """
        data["items_id"] = ticket_id
        data["itemtype"] = cls.__name__

        return Item.add(data)

    @classmethod
    def delete_item(cls, item_id: int) -> None:
        """Remove o vínculo de um ativo com um chamado.

        Args:
            item_id (int): ID do vínculo (Item_Ticket) a ser removido.

        Returns:
            list: Resultado da operação retornado pela API.
        """
        return Item.delete(item_id)

    @classmethod
    def get_items(cls, ticket_id: int, **kwargs: Any) -> list[dict[str, Any]]:
        """Retorna todos os ativos vinculados a um chamado.

        Args:
            ticket_id (int): ID do chamado no GLPI.
            **kwargs: Parâmetros extras repassados à chamada.

        Returns:
            list: Lista de ativos vinculados ao chamado.
        """
        return cls.get_sub_items(ticket_id, "Item_Ticket", **kwargs)

    # Métodos Actors ################################

    @classmethod
    def add_actor(cls, ticket_id: int, data: dict[str, Any]) -> int:
        """Adiciona um ator (requerente, técnico ou observador) a um chamado.

        Args:
            ticket_id (int): ID do chamado no GLPI.
            data (dict): Dados do ator. Campos comuns:
                - type (int): Tipo do ator — 1=Requerente, 2=Atribuído, 3=Observador.
                - users_id (int): ID do usuário a adicionar.
                - groups_id (int): ID do grupo a adicionar (alternativa ao users_id).

        Returns:
            list: Resultado da operação contendo o ID do ator criado.
        """
        data["items_id"] = ticket_id
        data["itemtype"] = cls.__name__

        return Actor.add(data)

    @classmethod
    def delete_actor(cls, actor_id: int) -> None:
        """Remove um ator de um chamado.

        Args:
            actor_id (int): ID do registro de ator a ser removido.

        Returns:
            list: Resultado da operação retornado pela API.
        """
        return Actor.delete(actor_id)

    @classmethod
    def get_actors(cls, ticket_id: int, **kwargs: Any) -> list[dict[str, Any]]:
        """Retorna todos os atores de um chamado.

        Args:
            ticket_id (int): ID do chamado no GLPI.
            **kwargs: Parâmetros extras repassados à chamada.

        Returns:
            list: Lista de atores do chamado.
        """
        return cls.get_sub_items(ticket_id, "Ticket_User", **kwargs)

    # Métodos LinkedTickets ################################

    @classmethod
    def add_linked_ticket(cls, ticket_id: int, data: dict[str, Any]) -> int:
        """Cria um vínculo entre dois chamados.

        Args:
            ticket_id (int): ID do chamado de origem no GLPI.
            data (dict): Dados do vínculo. Campos obrigatórios:
                - tickets_id_2 (int): ID do chamado de destino.
                - link (int): Tipo do vínculo — 1=Relacionado, 2=Duplicado,
                              3=Filho de, 4=Pai de.

        Returns:
            list: Resultado da operação contendo o ID do vínculo criado.
        """
        data["items_id"] = ticket_id
        data["itemtype"] = cls.__name__

        return LinkedTicket.add(data)

    @classmethod
    def delete_linked_ticket(cls, linked_ticket_id: int) -> None:
        """Remove o vínculo entre dois chamados.

        Args:
            linked_ticket_id (int): ID do vínculo (Ticket_Ticket) a ser removido.

        Returns:
            list: Resultado da operação retornado pela API.
        """
        return LinkedTicket.delete(linked_ticket_id)

    @classmethod
    def get_linked_tickets(cls, ticket_id: int, **kwargs: Any) -> list[dict[str, Any]]:
        """Retorna todos os chamados vinculados a um chamado.

        Args:
            ticket_id (int): ID do chamado no GLPI.
            **kwargs: Parâmetros extras repassados à chamada.

        Returns:
            list: Lista de vínculos entre chamados.
        """
        return cls.get_sub_items(ticket_id, "Ticket_Ticket", **kwargs)

    #####################################################

    """
    Adicionar métodos:
        Task: add_task, update_task, delete_task, get_tasks.
        Solution: *approve_solution
        Items: add_item, delete_item, get_items
        Actors: add_actor, delete_actor, get_actors
        LinkedTickets: add_linked_ticket, delete_linked_ticket, get_linked_tickets
    """
