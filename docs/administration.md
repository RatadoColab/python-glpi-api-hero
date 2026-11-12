# Administration

`glpi_api_hero.administration`: `User`, `Group`, `Entity`, `Profile`.

- `User`: `get_profiles`, `get_groups`, `get_emails`, `get_by_username`, `get_by_email`, `get_tickets(user_id,
  actor_type)` (documents and certificates readers too).
- `Group`: `get_users`, `add_user`, `delete_user`, `get_by_name` (exact match), `get_tickets(group_id, actor_type)`.
- `Entity`: tree lookups; `get_children` and `get_roots` read item rows by `entities_id`.
- `Profile`: `get_users`.

`actor_type` is `glpi_api_hero.core.constants.ActorType` (`REQUESTER`, `ASSIGNED`, `OBSERVER`).
