# Changelog

## Unreleased

### New
- The library now talks to GLPI 10 on its own, without the external `glpi-api` package. The transport sits behind a
  connector contract, so support for the GLPI 12 API can be added later without changing the models.
- Session handling in one place: connect once or use a session block, which
  closes the session by itself. The active profile and entity can be changed at any time.
- Models for the item types of the GLPI 10 menus, organized by menu: assets (computers, monitors, software, network
  equipment, printers, phones, racks, cables and more), assistance (tickets, changes, problems and recurring items),
  management (licenses, budgets, suppliers, contacts, contracts, documents, lines, certificates, domains,
  appliances and more), tools (projects, reminders, RSS feeds, knowledge base, reservations, saved searches),
  administration (users, groups, entities, profiles), dropdowns (locations, categories, states, manufacturers) and
  components (SIM cards).
- Tickets, changes and problems share the same operations: follow-ups, solutions, tasks, validations, actors, linked
  items, costs, documents and links between them, plus searches by requester, assignee, observer and group.
- Each model offers only the readers that GLPI supports for that item type, such as documents, notes, costs,
  network ports and tickets.
- Documents can be uploaded and downloaded safely, and the download never overwrites a file unless asked to.
- Any item type without a dedicated model can be used through the generic item factory.
- Complete create, read, update, delete and search operations in every model, with bulk versions of creation, update
  and deletion, plus listing of search options.
- Texts returned by searches come back as plain text (for example `<p>` instead of `&#60;p&#62;`), just like the
  texts returned when reading an item.
- Clear error types: not found, permission, rate limit, connection, partial operation and others, all derived from
  one base error. A bulk operation that only partly succeeds reports the result of each item.
- Type hints on the whole public API, so editors can autocomplete methods and arguments.
- Named constants for ticket actors and link types, and for the search fields used by the models.
- A migration guide that maps every old method name to the new one.
- Bulk creation and update of locations from any data source, using a conversion function (mapper) supplied by the
  caller.
- Choice of the field that identifies each location in the bulk update (the external code by default).
- Example mapper that turns a list of organizational units into GLPI locations.
- Example of asynchronous synchronization through RabbitMQ, with configurable queue names, rate limit handling and a
  queue for failed messages.
- Documentation, examples and code comments in English.

### Changed
- The package is now installed as glpi-api-hero; the name used in imports stays glpi_api_hero.
- Models are imported from the menu they belong to (for example the assets package), and the top-level package
  keeps only the session, the generic models, the exceptions and the version. Importing the library no longer has
  side effects.
- All public methods now use `snake_case` names and are called on the class, without creating objects.
- Results are uniform: creating returns the new id, updating and deleting return nothing, reading returns a
  dictionary and searching returns a list. An item that does not exist now raises an error instead of returning
  nothing.
- Connections verify the TLS certificate by default.
- Redirects from the GLPI server are no longer followed, so access tokens can never be sent to another host. Use the final API URL (for example https instead of http).
- Connection URLs with a user name or password, a query or a fragment are refused, and plain http URLs raise a warning.
- The conversion of a specific catalog of organizational units is no longer part of the library; it is now an example.
  Callers that used the bulk update with that format must pass the mapper from the example.
- The microservices and the Docker files are now examples, in the examples folder.
- The ticket dashboard is no longer part of the library; it is now an example and needs the `plotly` package.
- Follow-up search on a ticket, change or problem now returns only the follow-ups of that item.
- Ticket helpers for tasks, validations, actors, linked items and linked tickets were rewritten. Several of them sent
  data that GLPI ignored, so they now take the ticket id and the kind of actor or link explicitly.
- The old placeholder classes for ticket sub-items were removed; the same operations are methods of the ticket,
  change and problem models.

### Fixed
- Login with a user token now works; in the previous version the token was stored under a misspelled name and was
  never sent.
- Computer disks, the users of a location and the lookups by name and complete name use
  the correct GLPI fields.
- Methods that received a dictionary no longer change it.
- Texts with special characters (such as &) are returned as typed instead of HTML-encoded.
- Lookups by login, e-mail and group name now find the record by its exact text.
- Reading a page beyond the last result returns an empty list instead of an error.
- The bulk update of locations now updates a record that appears twice in the same list.
- Closing a session block that ended well no longer raises when the logout fails, so its result is kept.
- An invalid ticket role now raises an error instead of silently searching another role.
