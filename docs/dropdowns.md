# Dropdowns

`glpi_api_hero.dropdowns`: `Location`, `ITILCategory`, `State`, `Manufacturer`.

Tree-shaped dropdowns (`Location`, `ITILCategory`, `State`, also `Group` and `Entity`) share
`CommonTreeDropdown`: `get_by_name`, `get_by_complete_name`, `get_children`, `get_roots`.

`Location` adds `get_by_code`, `get_computers`, `get_network_equipments`, `get_tickets`, `get_users`,
`get_items_by_type(location_id, itemtype)` and bulk loading:

```python
from glpi_api_hero.dropdowns import Location

Location.add_from_list(records, mapper=my_mapper)
Location.update_from_list(records, mapper=my_mapper, key_field="code")
```

Without a mapper the records must already use GLPI field names. `examples/org_units/mapper.py` shows a mapper.
