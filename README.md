# python-glpi-api-hero

A Python library for working with GLPI (IT service management) from your own scripts and applications.

## What you can do

- Connect to a GLPI 10 server and work with its data in plain Python.
- Create, read, update, delete and search the items GLPI manages: tickets, changes, problems, computers and other
  assets, contracts, suppliers, documents, projects, users, groups, locations and more.
- Work with the details that belong to an item (follow-ups, tasks, linked assets, contracts, notes) straight from the
  item itself.
- Upload and download documents safely.
- Reach any item type that has no dedicated class through a generic helper.
- Get clear, library-specific errors instead of raw HTTP failures.

The connection layer is separate from the models, so support for newer GLPI API versions can be added without
changing the code that uses the library.

## Installation

```bash
pip install glpi-api-hero
```

To work on the library itself:

```bash
git clone <repository-url>
cd python-glpi-api-hero
pip install -e ".[dev]"
```

## First steps

You need the GLPI API URL, an application token and either a user token or a login and password.

```python
from glpi_api_hero import Glpi
from glpi_api_hero.assistance import Ticket

with Glpi.session("https://glpi.example.org/apirest.php", "APP_TOKEN", user_token="USER_TOKEN"):
    ticket_id = Ticket.add({"name": "Printer is down", "content": "Paper jam on floor 2"})
    Ticket.add_followup(ticket_id, {"content": "A technician is on the way"})
```

## Documentation

| Document | Content |
|---|---|
| [docs/getting-started.md](docs/getting-started.md) | Installation, sessions, profiles and entities |
| [docs/exceptions.md](docs/exceptions.md) | The errors the library raises and how to handle them |
| [docs/core.md](docs/core.md) | Generic operations shared by every item type |
| [docs/assets.md](docs/assets.md) | Computers, monitors, printers, network equipment and other assets |
| [docs/assistance.md](docs/assistance.md) | Tickets, changes, problems and recurrent items |
| [docs/management.md](docs/management.md) | Contracts, suppliers, documents, domains, licenses and more |
| [docs/tools.md](docs/tools.md) | Projects, reminders, knowledge base, reservations |
| [docs/administration.md](docs/administration.md) | Users, groups, entities and profiles |
| [docs/dropdowns.md](docs/dropdowns.md) | Locations, categories, statuses and manufacturers |
| [docs/components.md](docs/components.md) | Components such as SIM cards |
| [docs/migration.md](docs/migration.md) | What changed from the 0.1 releases |

## Examples

The `examples/` folder has ready-to-run examples:

- `examples/org_units/`: turns a list of organizational units into GLPI locations.
- `examples/rabbitmq_sync/`: a producer and a consumer that keep GLPI locations in sync through RabbitMQ, with rate
  limit handling and a queue for failed messages.
- `examples/ticket_dashboard/`: a visual dashboard of tickets by period and category.
