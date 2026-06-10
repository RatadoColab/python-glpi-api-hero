# Tickets

A classe `Ticket` gerencia chamados no GLPI e seus sub-recursos: acompanhamentos, soluções, validações, tarefas, ativos vinculados, atores e vínculos entre chamados.

Herda todos os métodos CRUD de `CommonDBTM` e adiciona métodos específicos para cada sub-recurso.

## CRUD básico (herdado de CommonDBTM)

### Criar chamado

```python
from glpi_api_hero import Ticket

ticket_data = {
    'name': 'Problema ao inicializar a máquina',
    'content': 'Descrição detalhada do problema...',
    'itilcategories_id': 672,
    'type': 1,        # 1=Incidente, 2=Requisição
    'priority': 3,    # 1=Muito baixa ... 6=Muito alta
    '_user_requester': 9407,
}
result = Ticket.add(ticket_data)
ticket_id = result[0]['id']
```

### Obter chamado por ID

```python
chamado = Ticket.get(ticket_id)
print(chamado['name'])
```

### Atualizar chamado

```python
Ticket.update({'id': ticket_id, 'priority': 5})
```

### Deletar chamado

```python
Ticket.delete([{'id': ticket_id}], force_purge=True)
```

### Listar todos os chamados (paginado)

```python
chamados = Ticket.get_all_items(range='0-49')
```

### Buscar chamados com critérios

```python
# Chamados que contêm "rede" no título
resultado = Ticket.search(criteria=[
    {'field': 1, 'searchtype': 'contains', 'value': 'rede'}
])
```

Ver [Busca avançada](#busca-avançada) para mais exemplos.

---

## FollowUps (Acompanhamentos)

Registros de comunicação adicionados ao longo da vida do chamado.

### Métodos

| Método | Parâmetros | Descrição |
|--------|-----------|-----------|
| `addFollowUp(ticket_id, data)` | `ticket_id`: ID do chamado; `data`: dict com campos do acompanhamento | Adiciona um acompanhamento |
| `updateFollowUp(followup_id, data)` | `followup_id`: ID do acompanhamento; `data`: campos a atualizar | Atualiza um acompanhamento |
| `deleteFollowUp(followup_id)` | `followup_id`: ID do acompanhamento | Remove um acompanhamento |
| `getFollowUps(ticket_id)` | `ticket_id`: ID do chamado | Lista todos os acompanhamentos |
| `searchFollowUps(**kwargs)` | Critérios de busca | Busca acompanhamentos por critérios |

**Campos comuns de `data`:**

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `content` | str | Texto do acompanhamento. **Obrigatório.** |
| `is_private` | int | `1` = privado, `0` = público. Padrão: `0`. |
| `requesttypes_id` | int | Tipo de canal (telefone, e-mail, etc.). |

### Exemplo

```python
# Adicionar
Ticket.addFollowUp(ticket_id, {
    'content': 'Estamos analisando o problema.',
    'is_private': 0,
})

# Listar
followups = Ticket.getFollowUps(ticket_id)

# Atualizar
Ticket.updateFollowUp(followup_id, {'content': 'Análise concluída.'})

# Remover
Ticket.deleteFollowUp(followup_id)
```

---

## Solutions (Soluções)

Registro da solução aplicada para encerrar o chamado.

### Métodos

| Método | Parâmetros | Descrição |
|--------|-----------|-----------|
| `addSolution(ticket_id, data)` | `ticket_id`: ID do chamado; `data`: dict com campos da solução | Adiciona uma solução |
| `updateSolution(solution_id, data)` | `solution_id`: ID da solução; `data`: campos a atualizar | Atualiza uma solução |
| `deleteSolution(solution_id)` | `solution_id`: ID da solução | Remove uma solução |
| `getSolution(ticket_id)` | `ticket_id`: ID do chamado | Retorna soluções do chamado |

**Campos comuns de `data`:**

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `content` | str | Texto da solução. **Obrigatório.** |
| `solutiontypes_id` | int | Tipo de solução cadastrado no GLPI. |

### Exemplo

```python
# Adicionar
Ticket.addSolution(ticket_id, {
    'content': 'Problema resolvido reinstalando o software.',
    'solutiontypes_id': 1,
})

# Consultar
solucao = Ticket.getSolution(ticket_id)

# Atualizar
Ticket.updateSolution(solution_id, {'content': 'Solução revisada.'})

# Remover
Ticket.deleteSolution(solution_id)
```

---

## Validations (Validações)

Fluxo de aprovação em que um usuário aprovador aceita ou recusa o chamado/solução.

### Métodos

| Método | Parâmetros | Descrição |
|--------|-----------|-----------|
| `addValidation(ticket_id, data)` | `ticket_id`: ID do chamado; `data`: dict com campos da validação | Solicita validação |
| `updateValidation(validation_id, data)` | `validation_id`: ID da validação; `data`: campos a atualizar | Atualiza validação |
| `deleteValidation(validation_id)` | `validation_id`: ID da validação | Remove validação |
| `getValidations(ticket_id, **kwargs)` | `ticket_id`: ID do chamado | Lista validações do chamado |

**Campos comuns de `data`:**

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `users_id_validate` | int | ID do usuário aprovador. **Obrigatório em `add`.** |
| `comment_submission` | str | Comentário enviado ao aprovador. |
| `status` | int | `2` = Aceito, `4` = Recusado. Usado em `update`. |
| `comment_validation` | str | Comentário do aprovador na resposta. |

### Exemplo

```python
# Solicitar validação
Ticket.addValidation(ticket_id, {
    'users_id_validate': 7,
    'comment_submission': 'Por favor, validar a solução proposta.',
})

# Listar validações
validacoes = Ticket.getValidations(ticket_id)

# Registrar resposta do aprovador
Ticket.updateValidation(validation_id, {
    'status': 2,  # 2=Aceito, 4=Recusado
    'comment_validation': 'Solução aprovada.',
})

# Remover
Ticket.deleteValidation(validation_id)
```

---

## Tasks (Tarefas)

Tarefas internas atribuídas a técnicos dentro de um chamado.

### Métodos

| Método | Parâmetros | Descrição |
|--------|-----------|-----------|
| `addTask(ticket_id, data)` | `ticket_id`: ID do chamado; `data`: dict com campos da tarefa | Adiciona uma tarefa |
| `updateTask(task_id, data)` | `task_id`: ID da tarefa; `data`: campos a atualizar | Atualiza uma tarefa |
| `deleteTask(task_id)` | `task_id`: ID da tarefa | Remove uma tarefa |
| `getTasks(ticket_id, **kwargs)` | `ticket_id`: ID do chamado | Lista tarefas do chamado |

**Campos comuns de `data`:**

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `content` | str | Descrição da tarefa. **Obrigatório.** |
| `state` | int | `0` = Informação, `1` = A fazer, `2` = Feito. |
| `taskcategories_id` | int | ID da categoria da tarefa. |
| `users_id_tech` | int | ID do técnico responsável. |
| `actiontime` | int | Tempo previsto/gasto em segundos. |

### Exemplo

```python
# Adicionar
Ticket.addTask(ticket_id, {
    'content': 'Verificar logs do servidor.',
    'state': 1,           # A fazer
    'users_id_tech': 42,
    'actiontime': 3600,   # 1 hora
})

# Listar
tarefas = Ticket.getTasks(ticket_id)

# Marcar como concluída
Ticket.updateTask(task_id, {'state': 2})

# Remover
Ticket.deleteTask(task_id)
```

---

## Items (Ativos vinculados)

Vínculo entre o chamado e ativos do parque (computadores, monitores, etc.).

### Métodos

| Método | Parâmetros | Descrição |
|--------|-----------|-----------|
| `addItem(ticket_id, data)` | `ticket_id`: ID do chamado; `data`: dict com `itemtype` e `items_id` | Vincula um ativo |
| `deleteItem(item_id)` | `item_id`: ID do vínculo (`Item_Ticket`) | Remove o vínculo |
| `getItems(ticket_id, **kwargs)` | `ticket_id`: ID do chamado | Lista ativos vinculados |

**Campos obrigatórios de `data`:**

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `itemtype` | str | Tipo do ativo: `'Computer'`, `'Monitor'`, `'Phone'`, etc. |
| `items_id` | int | ID do ativo no GLPI. |

### Exemplo

```python
# Vincular um computador
Ticket.addItem(ticket_id, {
    'itemtype': 'Computer',
    'items_id': 42,
})

# Listar ativos vinculados
itens = Ticket.getItems(ticket_id)

# Remover vínculo
Ticket.deleteItem(item_link_id)
```

---

## Actors (Atores)

Usuários e grupos associados ao chamado como requerente, técnico atribuído ou observador.

### Constantes de tipo

Definidas em `User`, mas usadas em qualquer contexto de ator:

| Constante | Valor | Descrição |
|-----------|-------|-----------|
| `User.REQUESTER` | `1` | Requerente (solicitante) |
| `User.ASSIGNED` | `2` | Técnico/grupo atribuído |
| `User.OBSERVER` | `3` | Observador |

### Métodos

| Método | Parâmetros | Descrição |
|--------|-----------|-----------|
| `addActor(ticket_id, data)` | `ticket_id`: ID do chamado; `data`: dict com tipo e ID do usuário/grupo | Adiciona um ator |
| `deleteActor(actor_id)` | `actor_id`: ID do registro de ator (`Ticket_User`) | Remove um ator |
| `getActors(ticket_id, **kwargs)` | `ticket_id`: ID do chamado | Lista atores do chamado |

**Campos comuns de `data`:**

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `type` | int | Tipo do ator: `1`, `2` ou `3` (ver constantes acima). |
| `users_id` | int | ID do usuário a associar. |
| `groups_id` | int | ID do grupo (alternativa a `users_id`). |

### Exemplo

```python
from glpi_api_hero import Ticket, User

# Adicionar técnico atribuído
Ticket.addActor(ticket_id, {
    'type': User.ASSIGNED,
    'users_id': 42,
})

# Adicionar grupo observador
Ticket.addActor(ticket_id, {
    'type': User.OBSERVER,
    'groups_id': 10,
})

# Listar atores
atores = Ticket.getActors(ticket_id)

# Remover ator
Ticket.deleteActor(actor_id)
```

---

## Linked Tickets (Chamados vinculados)

Vínculos entre chamados para expressar relações hierárquicas ou de equivalência.

### Tipos de vínculo

| Valor | Descrição |
|-------|-----------|
| `1` | Relacionado a |
| `2` | Duplicado de |
| `3` | Filho de |
| `4` | Pai de |

### Métodos

| Método | Parâmetros | Descrição |
|--------|-----------|-----------|
| `addLinkedTicket(ticket_id, data)` | `ticket_id`: ID de origem; `data`: dict com `tickets_id_2` e `link` | Cria vínculo |
| `deleteLinkedTicket(linked_ticket_id)` | `linked_ticket_id`: ID do vínculo (`Ticket_Ticket`) | Remove vínculo |
| `getLinkedTickets(ticket_id, **kwargs)` | `ticket_id`: ID do chamado | Lista vínculos |

### Exemplo

```python
# Vincular como chamado relacionado
Ticket.addLinkedTicket(ticket_id, {
    'tickets_id_2': 999,
    'link': 1,  # Relacionado a
})

# Listar vínculos
vinculados = Ticket.getLinkedTickets(ticket_id)

# Remover vínculo
Ticket.deleteLinkedTicket(linked_ticket_id)
```

---

## Busca avançada

O método `search` aceita o parâmetro `criteria` com uma lista de filtros:

```python
criteria = [
    {'field': <int>, 'searchtype': 'equals|contains|...', 'value': <valor>}
]
```

**Campos comuns de Ticket para busca:**

| field | Descrição |
|-------|-----------|
| `1` | Título (`name`) |
| `2` | ID |
| `4` | Requerente (usuário) |
| `5` | Atribuído a (usuário) |
| `12` | Status |
| `14` | Tipo (Incidente/Requisição) |
| `18` | Data de abertura |
| `66` | Observador |

**Exemplo — chamados abertos atribuídos a um técnico:**

```python
resultado = Ticket.search(
    criteria=[
        {'field': 5,  'searchtype': 'equals', 'value': 42},   # técnico ID 42
        {'field': 12, 'searchtype': 'equals', 'value': 1},    # status = novo
    ],
    range='0-29',
)
```

> Para descobrir o `field` correto use `Ticket.list_search_options(ticket_id)` contra um chamado existente.

---

## Referência rápida de constantes

| Constante | Valor | Contexto |
|-----------|-------|---------|
| `type=1` no chamado | Incidente | campo `type` em `Ticket.add` |
| `type=2` no chamado | Requisição | campo `type` em `Ticket.add` |
| `priority=1..6` | Muito baixa → Muito alta | campo `priority` em `Ticket.add/update` |
| `User.REQUESTER` | `1` | tipo de ator em `addActor` |
| `User.ASSIGNED` | `2` | tipo de ator em `addActor` |
| `User.OBSERVER` | `3` | tipo de ator em `addActor` |
| `state=0` (tarefa) | Informação | campo `state` em `addTask/updateTask` |
| `state=1` (tarefa) | A fazer | campo `state` em `addTask/updateTask` |
| `state=2` (tarefa) | Feito | campo `state` em `addTask/updateTask` |
| `status=2` (validação) | Aceito | campo `status` em `updateValidation` |
| `status=4` (validação) | Recusado | campo `status` em `updateValidation` |
