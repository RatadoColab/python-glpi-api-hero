# Assistance

`glpi_api_hero.assistance`: `Ticket`, `Change`, `Problem`, `TicketRecurrent`, `RecurrentChange`.

`Ticket`, `Change` and `Problem` share `CommonITILObject`. The first argument of the `add_*`/`get_*` methods is the
id of the ITIL object; `update_*`/`delete_*` take the id of the sub-item.

| Resource | Methods |
|---|---|
| Follow-ups | `add_followup`, `update_followup`, `delete_followup`, `get_followups`, `search_followups` |
| Solutions | `add_solution`, `update_solution`, `delete_solution`, `get_solutions`, `approve_solution`, `refuse_solution` |
| Tasks | `add_task`, `update_task`, `delete_task`, `get_tasks` |
| Validations (not on `Problem`) | `add_validation`, `update_validation`, `delete_validation`, `get_validations` |
| Actors | `add_actor(id, ActorKind, actor_id, ActorType)`, `delete_actor(link_id, kind)`, `get_actors` |
| Assets | `add_item(id, itemtype, items_id)`, `delete_item`, `get_items` |
| Costs | `add_cost`, `update_cost`, `delete_cost`, `get_costs` |
| Documents | `add_document`, `delete_document`, `get_documents` |
| Links | `link_ticket`, `link_problem`, `link_change`, `get_linked_*`, `unlink` |
| Search by actor | `get_by_requester`, `get_by_assigned`, `get_by_observer`, `get_by_group` |

```python
from glpi_api_hero.assistance import Ticket
from glpi_api_hero.core.constants import ActorKind, ActorType, LinkType

ticket_id = Ticket.add({"name": "Printer down", "content": "Paper jam"})
Ticket.add_actor(ticket_id, ActorKind.GROUP, 5, ActorType.ASSIGNED)
Ticket.link_ticket(ticket_id, 42, LinkType.DUPLICATE)
Ticket.approve_solution(ticket_id)
```

Combinations GLPI does not have raise `UnsupportedOperationError` (e.g. `Problem.add_validation`,
`Problem.link_problem`). `Ticket.get_satisfaction` is available on tickets only. GLPI closes the object on
`approve_solution` only when it is solved.
