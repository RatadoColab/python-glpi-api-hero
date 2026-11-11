# Assets

`glpi_api_hero.assets`: `Computer`, `Monitor`, `Software`, `NetworkEquipment`, `Peripheral`, `Printer`,
`CartridgeItem`, `ConsumableItem`, `Phone`, `Rack`, `Enclosure`, `PDU`, `PassiveDCEquipment`, `Unmanaged`, `Cable`.

Physical assets share `CommonAsset`: `get_by_name`, `get_by_serial`, `get_by_inventory_number`, `get_logs`,
`get_notes` (where GLPI enables notes). The other readers depend on the itemtype and follow the GLPI lists:

`get_infocom`, `get_network_ports`, `get_contracts`, `get_documents`, `get_certificates`, `get_domains`,
`get_appliances`, `get_clusters`, `get_software_versions`, `get_software_licenses`, `get_operating_systems`,
`get_disks`, `get_devices`, `get_sim_cards`, `get_racks`, `get_remote_managements`, `get_reservation_items`,
`get_tickets`.

```python
from glpi_api_hero.assets import Cable, Computer

Computer.get_devices(12, "Item_DeviceProcessor")   # one kind of component
Computer.get_devices(12)                           # every kind this itemtype can own
hasattr(Cable, "get_network_ports")                # False: cables have no network ports in GLPI
```

Specific methods: `Computer.get_virtual_machines`, `Computer.get_connections`, `Printer.get_cartridges`,
`CartridgeItem.get_cartridges`, `CartridgeItem.get_compatible_printer_models`, `ConsumableItem.get_consumables`,
`Rack.get_items`, `Rack.get_pdus`, `Enclosure.get_items`, `Software.get_versions`, `Software.get_licenses`,
`Software.get_installations`.

`get_tickets` returns the ticket link rows of the item (`Item_Ticket`). The matrix of capabilities per itemtype is
derived from `inc/define.php` of GLPI 10.0.26.
