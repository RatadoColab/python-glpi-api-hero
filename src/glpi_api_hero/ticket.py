from glpi_api_hero import CommonDBTM
from glpi_api_hero import ITILFollowup
from glpi_api_hero import ITILSolution
from glpi_api_hero import TicketValidation
from glpi_api_hero import Task
from glpi_api_hero import Item
from glpi_api_hero import Actor
from glpi_api_hero import LinkedTicket

class Ticket(CommonDBTM):

    # Métodos FollowUp ################################

    @classmethod
    def addFollowUp(cls, ticket_id: int, data: dict):
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
        data['items_id'] = ticket_id
        data['itemtype'] = cls.__name__

        return ITILFollowup.add(data)

    @classmethod
    def updateFollowUp(cls, followup_id: int, data: dict):
        """Atualiza um acompanhamento existente.

        Args:
            followup_id (int): ID do acompanhamento a ser atualizado.
            data (dict): Campos a atualizar. Campos comuns:
                - content (str): Novo texto do acompanhamento.
                - is_private (int): 1 para privado, 0 para público.

        Returns:
            list: Resultado da operação retornado pela API.
        """
        data['id'] = followup_id

        return ITILFollowup.update(data)

    @classmethod
    def deleteFollowUp(cls, followup_id: int):
        """Remove um acompanhamento de um chamado.

        Args:
            followup_id (int): ID do acompanhamento a ser removido.

        Returns:
            list: Resultado da operação retornado pela API.
        """
        return ITILFollowup.delete({'id': followup_id})

    @classmethod
    def getFollowUps(cls, ticket_id: int):
        """Retorna todos os acompanhamentos de um chamado.

        Args:
            ticket_id (int): ID do chamado no GLPI.

        Returns:
            list: Lista de acompanhamentos do chamado.
        """
        return cls.get_sub_items(ticket_id, 'ITILFollowup')

    @classmethod
    def searchFollowUps(cls, **kwargs):
        """Busca acompanhamentos com critérios variados.

        Args:
            **kwargs: Parâmetros de busca repassados à API (ex: criteria, range, sort).

        Returns:
            list: Lista de acompanhamentos encontrados.
        """
        return ITILFollowup.search(kwargs)

    # Métodos Solution ################################

    @classmethod
    def addSolution(cls, ticket_id: int, data: dict):
        """Adiciona uma solução a um chamado existente.

        Args:
            ticket_id (int): ID do chamado no GLPI.
            data (dict): Dados da solução. Campos comuns:
                - content (str): Texto da solução. Obrigatório.
                - solutiontypes_id (int): ID do tipo de solução.

        Returns:
            list: Resultado da operação contendo o ID da solução criada.
        """
        data['items_id'] = ticket_id
        data['itemtype'] = cls.__name__

        return ITILSolution.add(data)

    @classmethod
    def updateSolution(cls, solution_id: int, data: dict):
        """Atualiza uma solução existente.

        Args:
            solution_id (int): ID da solução a ser atualizada.
            data (dict): Campos a atualizar. Campos comuns:
                - content (str): Novo texto da solução.
                - solutiontypes_id (int): Novo tipo de solução.

        Returns:
            list: Resultado da operação retornado pela API.
        """
        data['id'] = solution_id

        return ITILSolution.update(data)

    @classmethod
    def deleteSolution(cls, solution_id: int):
        """Remove uma solução de um chamado.

        Args:
            solution_id (int): ID da solução a ser removida.

        Returns:
            list: Resultado da operação retornado pela API.
        """
        return ITILSolution.delete({'id': solution_id})

    @classmethod
    def getSolution(cls, ticket_id: int):
        """Retorna todas as soluções de um chamado.

        Args:
            ticket_id (int): ID do chamado no GLPI.

        Returns:
            list: Lista de soluções do chamado.
        """
        return cls.get_sub_items(ticket_id, 'ITILSolution')

    @classmethod
    def ApprovalSolution(cls, solution_id: int):
        """Registra a aprovação de uma solução existente.

        Args:
            solution_id (int): ID da solução a ser aprovada.

        Returns:
            list: Resultado da operação retornado pela API.
        """
        return ITILSolution.add(solution_id)

    # Métodos Validation ################################

    @classmethod
    def addValidation(cls, ticket_id: int, data: dict):
        """Solicita validação de um chamado a um usuário aprovador.

        Args:
            ticket_id (int): ID do chamado no GLPI.
            data (dict): Dados da validação. Campos comuns:
                - users_id_validate (int): ID do usuário que deve validar. Obrigatório.
                - comment_submission (str): Comentário enviado ao aprovador.

        Returns:
            list: Resultado da operação contendo o ID da validação criada.
        """
        data['items_id'] = ticket_id
        data['itemtype'] = cls.__name__

        return TicketValidation.add(data)

    @classmethod
    def updateValidation(cls, validation_id: int, data: dict):
        """Atualiza uma solicitação de validação existente.

        Args:
            validation_id (int): ID da validação a ser atualizada.
            data (dict): Campos a atualizar. Campos comuns:
                - status (int): Novo status — 2=Aceito, 4=Recusado.
                - comment_validation (str): Comentário do aprovador.

        Returns:
            list: Resultado da operação retornado pela API.
        """
        data['id'] = validation_id

        return TicketValidation.update(data)

    @classmethod
    def deleteValidation(cls, validation_id: int):
        """Remove uma solicitação de validação de um chamado.

        Args:
            validation_id (int): ID da validação a ser removida.

        Returns:
            list: Resultado da operação retornado pela API.
        """
        return TicketValidation.delete({'id': validation_id})

    @classmethod
    def getValidations(cls, ticket_id: int, **kwargs):
        """Retorna todas as validações de um chamado.

        Args:
            ticket_id (int): ID do chamado no GLPI.
            **kwargs: Parâmetros extras repassados à chamada.

        Returns:
            list: Lista de validações do chamado.
        """
        return cls.get_sub_items(ticket_id, 'TicketValidation', **kwargs)

    # Métodos Task ################################

    @classmethod
    def addTask(cls, ticket_id: int, data: dict):
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
        data['items_id'] = ticket_id
        data['itemtype'] = cls.__name__

        return Task.add(data)

    @classmethod
    def updateTask(cls, task_id: int, data: dict):
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
        data['id'] = task_id

        return Task.update(data)

    @classmethod
    def deleteTask(cls, task_id: int):
        """Remove uma tarefa de um chamado.

        Args:
            task_id (int): ID da tarefa a ser removida.

        Returns:
            list: Resultado da operação retornado pela API.
        """
        return Task.delete({'id': task_id})

    @classmethod
    def getTasks(cls, ticket_id: int, **kwargs):
        """Retorna todas as tarefas de um chamado.

        Args:
            ticket_id (int): ID do chamado no GLPI.
            **kwargs: Parâmetros extras repassados à chamada.

        Returns:
            list: Lista de tarefas do chamado.
        """
        return cls.get_sub_items(ticket_id, 'TicketTask', **kwargs)

    # Métodos Item ################################

    @classmethod
    def addItem(cls, ticket_id: int, data: dict):
        """Vincula um ativo (item) a um chamado existente.

        Args:
            ticket_id (int): ID do chamado no GLPI.
            data (dict): Dados do vínculo. Campos obrigatórios:
                - itemtype (str): Tipo do ativo (ex: 'Computer', 'Monitor').
                - items_id (int): ID do ativo no GLPI.

        Returns:
            list: Resultado da operação contendo o ID do vínculo criado.
        """
        data['items_id'] = ticket_id
        data['itemtype'] = cls.__name__

        return Item.add(data)

    @classmethod
    def deleteItem(cls, item_id: int):
        """Remove o vínculo de um ativo com um chamado.

        Args:
            item_id (int): ID do vínculo (Item_Ticket) a ser removido.

        Returns:
            list: Resultado da operação retornado pela API.
        """
        return Item.delete({'id': item_id})

    @classmethod
    def getItems(cls, ticket_id: int, **kwargs):
        """Retorna todos os ativos vinculados a um chamado.

        Args:
            ticket_id (int): ID do chamado no GLPI.
            **kwargs: Parâmetros extras repassados à chamada.

        Returns:
            list: Lista de ativos vinculados ao chamado.
        """
        return cls.get_sub_items(ticket_id, 'Item_Ticket', **kwargs)

    # Métodos Actors ################################

    @classmethod
    def addActor(cls, ticket_id: int, data: dict):
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
        data['items_id'] = ticket_id
        data['itemtype'] = cls.__name__

        return Actor.add(data)

    @classmethod
    def deleteActor(cls, actor_id: int):
        """Remove um ator de um chamado.

        Args:
            actor_id (int): ID do registro de ator a ser removido.

        Returns:
            list: Resultado da operação retornado pela API.
        """
        return Actor.delete({'id': actor_id})

    @classmethod
    def getActors(cls, ticket_id: int, **kwargs):
        """Retorna todos os atores de um chamado.

        Args:
            ticket_id (int): ID do chamado no GLPI.
            **kwargs: Parâmetros extras repassados à chamada.

        Returns:
            list: Lista de atores do chamado.
        """
        return cls.get_sub_items(ticket_id, 'Ticket_User', **kwargs)

    # Métodos LinkedTickets ################################

    @classmethod
    def addLinkedTicket(cls, ticket_id: int, data: dict):
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
        data['items_id'] = ticket_id
        data['itemtype'] = cls.__name__

        return LinkedTicket.add(data)

    @classmethod
    def deleteLinkedTicket(cls, linked_ticket_id: int):
        """Remove o vínculo entre dois chamados.

        Args:
            linked_ticket_id (int): ID do vínculo (Ticket_Ticket) a ser removido.

        Returns:
            list: Resultado da operação retornado pela API.
        """
        return LinkedTicket.delete({'id': linked_ticket_id})

    @classmethod
    def getLinkedTickets(cls, ticket_id: int, **kwargs):
        """Retorna todos os chamados vinculados a um chamado.

        Args:
            ticket_id (int): ID do chamado no GLPI.
            **kwargs: Parâmetros extras repassados à chamada.

        Returns:
            list: Lista de vínculos entre chamados.
        """
        return cls.get_sub_items(ticket_id, 'Ticket_Ticket', **kwargs)

    #####################################################

    '''
    Adicionar métodos:
        Task: addTask, updateTask, deleteTask, getTasks.
        Solution: *ApprovalSolution
        Items: addItem, deleteItem, getItems
        Actors: addActor, deleteActor, getActors
        LinkedTickets: addLinkedTicket, deleteLinkedTicket, getLinkedTickets
    '''
