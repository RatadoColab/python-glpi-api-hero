# Changelog

## Unreleased

### New
- Bulk creation and update of locations from any data source, using a conversion function (mapper) supplied by the
  caller.
- Choice of the field that identifies each location in the bulk update (the external code by default).
- Example mapper that turns a list of organizational units into GLPI locations.
- Example of asynchronous synchronization through RabbitMQ, with configurable queue names, rate limit handling and a
  queue for failed messages.
- Documentation, examples and code comments in English.

### Changed
- The conversion of a specific catalog of organizational units is no longer part of the library; it is now an example.
  Callers that used the bulk update with that format must pass the mapper from the example.
- The microservices and the Docker files are now examples, in the examples folder.
