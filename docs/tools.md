# Tools

`glpi_api_hero.tools`: `Project`, `Reminder`, `RSSFeed`, `KnowbaseItem`, `ReservationItem`, `SavedSearch`.

- `Project`: `get_tasks`, `add_task`, `update_task`, `delete_task`, `get_team`, `add_team_member`,
  `delete_team_member`, `get_items`, `get_costs`, `get_itil_objects` (plus contracts, documents, notes, logs).
- `Reminder` and `KnowbaseItem`: `get_targets` returns the rows of the entity, group, profile and user relations, each
  with `kind` and `target_id` (`[]` when there is no target). `KnowbaseItem.get_items` lists the linked items.
- `ReservationItem`: `get_reservations`, `add_reservation`, `delete_reservation`.
- `RSSFeed`, `SavedSearch`: generic operations only.
