# Migration guide

This guide lists what changed between the 0.1 releases and the GLPI 10 refactor. Every public method is now
`snake_case`, typed, and a class method (models are never instantiated).

The `new` column reads `module:Class.method`, or `removed (<reason>)` when there is no replacement.

## Imports

| old | new |
|---|---|
| `from glpi_api_hero import Computer` (and every flat model import) | `from glpi_api_hero.assets import Computer` |
| `from glpi_api_hero import Group, User` | `from glpi_api_hero.administration import Group, User` |
| `from glpi_api_hero import Location` | `from glpi_api_hero.dropdowns import Location` |
| `from glpi_api_hero import Ticket` | `from glpi_api_hero.assistance import Ticket` |
| `import glpi_api` (external package) | removed (the library has its own `requests` transport) |

## Renamed, moved and removed API

| old | new |
|---|---|
| `User.getAllProfiles` | `glpi_api_hero.administration:User.get_profiles` |
| `User.getAllGroups` | `glpi_api_hero.administration:User.get_groups` |
| `User.getAllTickets` | `glpi_api_hero.administration:User.get_tickets` |
| `User.getByUsername` | `glpi_api_hero.administration:User.get_by_username` |
| `User.getByEmail` | `glpi_api_hero.administration:User.get_by_email` |
| `Group.getAllUsers` | `glpi_api_hero.administration:Group.get_users` |
| `Group.addUser` | `glpi_api_hero.administration:Group.add_user` |
| `Group.deleteUser` | `glpi_api_hero.administration:Group.delete_user` |
| `Group.getAllTickets` | `glpi_api_hero.administration:Group.get_tickets` |
| `Group.getByName` | `glpi_api_hero.administration:Group.get_by_name` |
| `Computer.getByName` | `glpi_api_hero.assets:Computer.get_by_name` |
| `Computer.getBySerial` | `glpi_api_hero.assets:Computer.get_by_serial` |
| `Computer.getByPatrimonio` | `glpi_api_hero.assets:Computer.get_by_inventory_number` |
| `Computer.getOperatingSystem` | `glpi_api_hero.assets:Computer.get_operating_system` |
| `Computer.getSoftwares` | `glpi_api_hero.assets:Computer.get_softwares` |
| `Computer.getNetworkPorts` | `glpi_api_hero.assets:Computer.get_network_ports` |
| `Computer.getProcessors` | `glpi_api_hero.assets:Computer.get_processors` |
| `Computer.getMemories` | `glpi_api_hero.assets:Computer.get_memories` |
| `Computer.getDisks` | `glpi_api_hero.assets:Computer.get_disks` |
| `Computer.getHardDrives` | `glpi_api_hero.assets:Computer.get_hard_drives` |
| `Computer.getVirtualMachines` | `glpi_api_hero.assets:Computer.get_virtual_machines` |
| `Computer.getTickets` | `glpi_api_hero.assets:Computer.get_tickets` |
| `Computer.getInfocom` | `glpi_api_hero.assets:Computer.get_infocom` |
| `Computer.getLogs` | `glpi_api_hero.assets:Computer.get_logs` |
| `Location.getByName` | `glpi_api_hero.dropdowns:Location.get_by_name` |
| `Location.getByCode` | `glpi_api_hero.dropdowns:Location.get_by_code` |
| `Location.getByCompleteName` | `glpi_api_hero.dropdowns:Location.get_by_complete_name` |
| `Location.getChildren` | `glpi_api_hero.dropdowns:Location.get_children` |
| `Location.getRoots` | `glpi_api_hero.dropdowns:Location.get_roots` |
| `Location.getComputers` | `glpi_api_hero.dropdowns:Location.get_computers` |
| `Location.getNetworkEquipments` | `glpi_api_hero.dropdowns:Location.get_network_equipments` |
| `Location.getTickets` | `glpi_api_hero.dropdowns:Location.get_tickets` |
| `Location.getUsers` | `glpi_api_hero.dropdowns:Location.get_users` |
| `Location.addFromList` | `glpi_api_hero.dropdowns:Location.add_from_list` |
| `Location.updateFromList` | `glpi_api_hero.dropdowns:Location.update_from_list` |
| `Location.getLogs` | `glpi_api_hero.dropdowns:Location.get_logs` |
| `Ticket.addFollowUp` | `glpi_api_hero.assistance:Ticket.add_followup` |
| `Ticket.updateFollowUp` | `glpi_api_hero.assistance:Ticket.update_followup` |
| `Ticket.deleteFollowUp` | `glpi_api_hero.assistance:Ticket.delete_followup` |
| `Ticket.getFollowUps` | `glpi_api_hero.assistance:Ticket.get_followups` |
| `Ticket.searchFollowUps` | `glpi_api_hero.assistance:Ticket.search_followups` |
| `Ticket.addSolution` | `glpi_api_hero.assistance:Ticket.add_solution` |
| `Ticket.updateSolution` | `glpi_api_hero.assistance:Ticket.update_solution` |
| `Ticket.deleteSolution` | `glpi_api_hero.assistance:Ticket.delete_solution` |
| `Ticket.getSolution` | `glpi_api_hero.assistance:Ticket.get_solutions` |
| `Ticket.ApprovalSolution` | `glpi_api_hero.assistance:Ticket.approve_solution` |
| `Ticket.addValidation` | `glpi_api_hero.assistance:Ticket.add_validation` |
| `Ticket.updateValidation` | `glpi_api_hero.assistance:Ticket.update_validation` |
| `Ticket.deleteValidation` | `glpi_api_hero.assistance:Ticket.delete_validation` |
| `Ticket.getValidations` | `glpi_api_hero.assistance:Ticket.get_validations` |
| `Ticket.addTask` | `glpi_api_hero.assistance:Ticket.add_task` |
| `Ticket.updateTask` | `glpi_api_hero.assistance:Ticket.update_task` |
| `Ticket.deleteTask` | `glpi_api_hero.assistance:Ticket.delete_task` |
| `Ticket.getTasks` | `glpi_api_hero.assistance:Ticket.get_tasks` |
| `Ticket.addItem` | `glpi_api_hero.assistance:Ticket.add_item` |
| `Ticket.deleteItem` | `glpi_api_hero.assistance:Ticket.delete_item` |
| `Ticket.getItems` | `glpi_api_hero.assistance:Ticket.get_items` |
| `Ticket.addActor` | `glpi_api_hero.assistance:Ticket.add_actor` |
| `Ticket.deleteActor` | `glpi_api_hero.assistance:Ticket.delete_actor` |
| `Ticket.getActors` | `glpi_api_hero.assistance:Ticket.get_actors` |
| `Ticket.addLinkedTicket` | `glpi_api_hero.assistance:Ticket.add_linked_ticket` |
| `Ticket.deleteLinkedTicket` | `glpi_api_hero.assistance:Ticket.delete_linked_ticket` |
| `Ticket.getLinkedTickets` | `glpi_api_hero.assistance:Ticket.get_linked_tickets` |
| `Group.REQUESTER`, `Group.ASSIGNED`, `Group.OBSERVER` | `glpi_api_hero.core.constants:ActorType` |
| `User.REQUESTER`, `User.ASSIGNED`, `User.OBSERVER` | `glpi_api_hero.core.constants:ActorType` |
| `CommonDBTM.get_all_items` | `glpi_api_hero.core.common_dbtm:CommonDBTM.get_all` |
| `CommonDBTM.add (list of items)` | `glpi_api_hero.core.common_dbtm:CommonDBTM.add_many` |
| `CommonDBTM.update (list of items)` | `glpi_api_hero.core.common_dbtm:CommonDBTM.update_many` |
| `CommonDBTM.delete (list of items)` | `glpi_api_hero.core.common_dbtm:CommonDBTM.delete_many` |
| `CommonDBTM.list_search_options` | `glpi_api_hero.core.common_dbtm:CommonDBTM.search_options` |
| `ApiCommunication.setConnectionParameters + initSession` | `glpi_api_hero:Glpi.connect` |
| `ApiCommunication.killSession` | `glpi_api_hero:Glpi.disconnect` |
| `ApiCommunication.setProfileEntity` | `glpi_api_hero:Glpi.set_profile_entity` |
| `ApiCommunication.getLoggedUser` | `glpi_api_hero:Glpi.logged_user` |
| `ApiCommunication.getConn` | `glpi_api_hero:Glpi.connector` |
| `ApiCommunication.call` | removed (errors are already library exceptions; call the connector directly) |
| `ApiCommunication.initSession` | removed (use `Glpi.connect` or the `Glpi.session` context manager) |
| `ApiConnectionError` | `glpi_api_hero.exceptions:GlpiConnectionError` |
| `ApiOperationError` | `glpi_api_hero.exceptions:GlpiAPIError (and its subclasses)` |
| `ApiRateLimitError` | `glpi_api_hero.exceptions:RateLimitError` |
| `Actor, Item, Task, LinkedTicket, ITILFollowup, ITILSolution, TicketValidation` | removed (provisional private classes in `core/_legacy_children.py`; typed replacements in phase 05) |
| `Cluster, NetworkEquipment (stubs)` | removed (provisional private classes; typed replacements in phases 06 to 08) |
| `TicketDashboard` | removed from the package (now an example: `examples/ticket_dashboard/ticket_dashboard.py`) |

## Behavior changes already in effect

- Session: use `Glpi.connect(...)` or the `Glpi.session(...)` context manager; TLS is verified by default.
- Return values are normalized: `add` returns the new id (`int`), `add_many` returns `list[int]`, `update` and
  `delete` return `None`, and a missing item raises `NotFoundError`.
- Failed bulk writes raise `PartialOperationError` with the per-item results.

The distribution name is now `glpi-api-hero` (`pip install glpi-api-hero`); the import name is still `glpi_api_hero`.
