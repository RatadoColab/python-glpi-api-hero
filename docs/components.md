# Components

`glpi_api_hero.components`: `DeviceSimcard` (the SIM card model) with `get_installations`, which lists where it is
installed (`Item_DeviceSimcard`). Other `Device*` components are reachable through `GenericItem.of(...)` and through
`get_devices` on the assets that can own them.
