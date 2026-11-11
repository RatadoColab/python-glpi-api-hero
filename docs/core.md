# Core

## CommonDBTM

Base of every model (`glpi_api_hero.core.common_dbtm`). Return values do not depend on the API version.

| Method | Returns |
|---|---|
| `get(id, **params)` | `dict` (`NotFoundError` when missing) |
| `get_all(**params)` | `list[dict]` |
| `search(criteria, forcedisplay=None, metacriteria=None, **params)` | `list[dict]` rows indexed by field id |
| `add(data)` / `add_many(items)` | `int` / `list[int]` |
| `update(id, data)` / `update_many(items)` | `None` |
| `delete(id, force_purge=False)` / `delete_many(ids)` | `None` |
| `get_sub_items(id, sub_itemtype)`, `add_sub_item`, `update_sub_item`, `delete_sub_item` | sub-item operations |
| `search_options()`, `field_id(uid)`, `field_uid(id)` | search option helpers |

Search criteria: `[{"field": 1, "searchtype": "contains", "value": "srv"}]`. Input dicts are never modified.

## GenericItem

`GenericItem.of("Itemtype")` returns a model for any itemtype, including plugin itemtypes. The itemtype name is
validated before any request.

```python
from glpi_api_hero import GenericItem

Line = GenericItem.of("Line")
Line.get(3)
```

## Connector

`glpi_api_hero.core.connector.Connector` is the contract between the models and the GLPI API;
`LegacyRestConnector` implements it for the REST API of GLPI 10. `Glpi.connector()` returns the active one.
Document upload and download live on the connector (`upload_document`, `download_document`).

## Capability mixins

`glpi_api_hero.core.capabilities` has one mixin per kind of sub-item (`HasInfocom`, `HasDocuments`, `HasTickets`...).
A model combines only the mixins GLPI allows for its itemtype, so unsupported readers do not exist.
