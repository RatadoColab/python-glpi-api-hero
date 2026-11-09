# Sub-recursos

Classes auxiliares usadas internamente pelos métodos de `Ticket`. Todas herdam `CommonDBTM` e podem ser operadas diretamente quando necessário, mas o uso habitual é via `Ticket`.

---

## Actor (`Ticket_User`)

Representa o vínculo entre um usuário/grupo e um chamado em um papel específico (requerente, atribuído, observador).

`_glpi_name = 'Ticket_User'`

**Uso habitual via Ticket:**

```python
Ticket.addActor(ticket_id, {'type': 1, 'users_id': 42})
Ticket.getActors(ticket_id)
Ticket.deleteActor(actor_id)
```

**Uso direto:**

```python
from glpi_api_hero import Actor

Actor.add({'items_id': ticket_id, 'itemtype': 'Ticket', 'type': 2, 'users_id': 42})
atores = Actor.search(criteria=[{'field': 4, 'searchtype': 'equals', 'value': ticket_id}])
```

Ver [Actors em tickets.md](tickets.md#actors-atores) para campos e constantes de tipo.

---

## Item (`Item_Ticket`)

Representa o vínculo entre um ativo (computador, monitor, etc.) e um chamado.

`_glpi_name = 'Item_Ticket'`

**Uso habitual via Ticket:**

```python
Ticket.addItem(ticket_id, {'itemtype': 'Computer', 'items_id': 7})
Ticket.getItems(ticket_id)
Ticket.deleteItem(item_link_id)
```

**Uso direto:**

```python
from glpi_api_hero import Item

Item.add({'items_id': ticket_id, 'itemtype': 'Ticket', 'items_id_2': 7, 'itemtype_2': 'Computer'})
```

Ver [Items em tickets.md](tickets.md#items-ativos-vinculados) para campos obrigatórios.

---

## Task (`TicketTask`)

Representa uma tarefa interna atribuída a um técnico dentro de um chamado.

`_glpi_name = 'TicketTask'`

**Uso habitual via Ticket:**

```python
Ticket.addTask(ticket_id, {'content': 'Verificar logs.', 'state': 1, 'users_id_tech': 42})
Ticket.getTasks(ticket_id)
Ticket.updateTask(task_id, {'state': 2})
Ticket.deleteTask(task_id)
```

**Estados de tarefa:**

| Valor | Descrição |
|-------|-----------|
| `0` | Informação |
| `1` | A fazer |
| `2` | Feito |

Ver [Tasks em tickets.md](tickets.md#tasks-tarefas) para todos os campos.

---

## LinkedTicket (`Ticket_Ticket`)

Representa o vínculo entre dois chamados.

`_glpi_name = 'Ticket_Ticket'`

**Uso habitual via Ticket:**

```python
Ticket.addLinkedTicket(ticket_id, {'tickets_id_2': 999, 'link': 1})
Ticket.getLinkedTickets(ticket_id)
Ticket.deleteLinkedTicket(linked_ticket_id)
```

**Tipos de vínculo (`link`):**

| Valor | Descrição |
|-------|-----------|
| `1` | Relacionado a |
| `2` | Duplicado de |
| `3` | Filho de |
| `4` | Pai de |

Ver [Linked Tickets em tickets.md](tickets.md#linked-tickets-chamados-vinculados) para mais detalhes.

---

## Classes stub (a implementar, se necessário)

As classes abaixo herdam `CommonDBTM` e os métodos CRUD básicos funcionam normalmente. Métodos específicos de domínio ainda não foram implementados.

| Classe | `_glpi_name` | Status |
|--------|-------------|--------|
| `ITILFollowup` | `ITILFollowup` (padrão) | Stub — apenas CRUD herdado |
| `ITILSolution` | `ITILSolution` (padrão) | Stub — apenas CRUD herdado |
| `TicketValidation` | `TicketValidation` (padrão) | Stub — apenas CRUD herdado |
| `Cluster` | `Cluster` (padrão) | Stub — apenas CRUD herdado |
| `NetworkEquipment` | `NetworkEquipment` (padrão) | Stub — apenas CRUD herdado |

O uso via `Ticket` (`addFollowUp`, `addSolution`, `addValidation`) já funciona porque `Ticket` injeta os campos `items_id` e `itemtype` e chama o `add` herdado dessas classes diretamente.

```python
# Funcionam via Ticket (o CRUD herdado é chamado internamente):
Ticket.addFollowUp(ticket_id, {'content': 'Acompanhamento.'})
Ticket.addSolution(ticket_id, {'content': 'Solução aplicada.'})
Ticket.addValidation(ticket_id, {'users_id_validate': 7})

# CRUD direto também funciona (sem validações de domínio):
from glpi_api_hero import Cluster
cluster = Cluster.get(42)
todos   = Cluster.get_all_items(range='0-49')
```
