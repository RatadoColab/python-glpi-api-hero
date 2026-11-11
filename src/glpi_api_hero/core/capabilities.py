"""Capability mixins of the GLPI items: each one adds the sub-item readers an itemtype supports.

GLPI decides which itemtypes accept each kind of sub-item in the ``$CFG_GLPI["<x>_types"]`` lists of
``inc/define.php`` (copied as test data in ``tests/unit/data/asset_capabilities.json``).
A model combines only the mixins its itemtype is listed for, so unsupported methods do not exist
(``hasattr(Cable, "get_infocom")`` is false) instead of failing at run time.

The mixins are reused by every batch of models (assets, management, tools).
"""

from __future__ import annotations

from typing import Any

from glpi_api_hero.core.common_dbtm import CommonDBTM
from glpi_api_hero.exceptions import UnsupportedOperationError

# Item_Device* itemtypes and the itemtypes that may own them (``itemdevice<x>_types``; ``*`` = any)
ITEM_DEVICE_TYPES: dict[str, tuple[str, ...]] = {
    "Item_DeviceMotherboard": ("Computer", "Phone"),
    "Item_DeviceFirmware": ("Computer", "Peripheral", "Phone", "NetworkEquipment", "Printer"),
    "Item_DeviceProcessor": ("Computer", "Phone"),
    "Item_DeviceMemory": ("Computer", "NetworkEquipment", "Peripheral", "Printer", "Phone"),
    "Item_DeviceHardDrive": ("Computer", "Peripheral", "NetworkEquipment", "Printer", "Phone"),
    "Item_DeviceNetworkCard": ("Computer", "NetworkEquipment", "Peripheral", "Phone", "Printer"),
    "Item_DeviceDrive": ("Computer", "Peripheral"),
    "Item_DeviceBattery": ("Computer", "Peripheral", "Phone", "Printer"),
    "Item_DeviceGraphicCard": ("Computer", "Phone"),
    "Item_DeviceSoundCard": ("Computer",),
    "Item_DeviceControl": ("Computer", "Peripheral", "Phone", "NetworkEquipment", "Printer"),
    "Item_DevicePci": ("*",),
    "Item_DevicePowerSupply": ("Computer", "NetworkEquipment", "Peripheral", "Enclosure", "Phone"),
    "Item_DeviceGeneric": ("*",),
    "Item_DeviceSimcard": ("Computer", "Peripheral", "Phone", "NetworkEquipment", "Printer"),
    "Item_DeviceSensor": ("Computer", "Peripheral", "Phone"),
    "Item_DeviceCamera": ("Computer", "Phone"),
}


class HasInfocom(CommonDBTM):
    """Adds ``get_infocom``."""

    @classmethod
    def get_infocom(cls, items_id: int, **params: Any) -> list[dict[str, Any]]:
        """Return the financial information (``Infocom``) of one item.

        Args:
            items_id: Item id.
            **params: Extra API parameters (``range``...).

        Returns:
            The rows (empty list when there is none).
        """
        return cls.get_sub_items(items_id, "Infocom", **params)


class HasNetworkPorts(CommonDBTM):
    """Adds ``get_network_ports``."""

    @classmethod
    def get_network_ports(cls, items_id: int, **params: Any) -> list[dict[str, Any]]:
        """Return the network ports of one item.

        Args:
            items_id: Item id.
            **params: Extra API parameters (``range``...).

        Returns:
            The rows (empty list when there is none).
        """
        return cls.get_sub_items(items_id, "NetworkPort", **params)


class HasContracts(CommonDBTM):
    """Adds ``get_contracts``."""

    @classmethod
    def get_contracts(cls, items_id: int, **params: Any) -> list[dict[str, Any]]:
        """Return the contract links (``Contract_Item``) of one item.

        Args:
            items_id: Item id.
            **params: Extra API parameters (``range``...).

        Returns:
            The rows (empty list when there is none).
        """
        return cls.get_sub_items(items_id, "Contract_Item", **params)


class HasDocuments(CommonDBTM):
    """Adds ``get_documents``."""

    @classmethod
    def get_documents(cls, items_id: int, **params: Any) -> list[dict[str, Any]]:
        """Return the document links (``Document_Item``) of one item.

        Args:
            items_id: Item id.
            **params: Extra API parameters (``range``...).

        Returns:
            The rows (empty list when there is none).
        """
        return cls.get_sub_items(items_id, "Document_Item", **params)


class HasCertificates(CommonDBTM):
    """Adds ``get_certificates``."""

    @classmethod
    def get_certificates(cls, items_id: int, **params: Any) -> list[dict[str, Any]]:
        """Return the certificate links (``Certificate_Item``) of one item.

        Args:
            items_id: Item id.
            **params: Extra API parameters (``range``...).

        Returns:
            The rows (empty list when there is none).
        """
        return cls.get_sub_items(items_id, "Certificate_Item", **params)


class HasDomains(CommonDBTM):
    """Adds ``get_domains``."""

    @classmethod
    def get_domains(cls, items_id: int, **params: Any) -> list[dict[str, Any]]:
        """Return the domain links (``Domain_Item``) of one item.

        Args:
            items_id: Item id.
            **params: Extra API parameters (``range``...).

        Returns:
            The rows (empty list when there is none).
        """
        return cls.get_sub_items(items_id, "Domain_Item", **params)


class HasAppliances(CommonDBTM):
    """Adds ``get_appliances``."""

    @classmethod
    def get_appliances(cls, items_id: int, **params: Any) -> list[dict[str, Any]]:
        """Return the appliance links (``Appliance_Item``) of one item.

        Args:
            items_id: Item id.
            **params: Extra API parameters (``range``...).

        Returns:
            The rows (empty list when there is none).
        """
        return cls.get_sub_items(items_id, "Appliance_Item", **params)


class HasClusters(CommonDBTM):
    """Adds ``get_clusters``."""

    @classmethod
    def get_clusters(cls, items_id: int, **params: Any) -> list[dict[str, Any]]:
        """Return the cluster links (``Item_Cluster``) of one item.

        Args:
            items_id: Item id.
            **params: Extra API parameters (``range``...).

        Returns:
            The rows (empty list when there is none).
        """
        return cls.get_sub_items(items_id, "Item_Cluster", **params)


class HasOperatingSystem(CommonDBTM):
    """Adds ``get_operating_systems``."""

    @classmethod
    def get_operating_systems(cls, items_id: int, **params: Any) -> list[dict[str, Any]]:
        """Return the operating system records (``Item_OperatingSystem``) of one item.

        Args:
            items_id: Item id.
            **params: Extra API parameters (``range``...).

        Returns:
            The rows (empty list when there is none).
        """
        return cls.get_sub_items(items_id, "Item_OperatingSystem", **params)


class HasDisks(CommonDBTM):
    """Adds ``get_disks``."""

    @classmethod
    def get_disks(cls, items_id: int, **params: Any) -> list[dict[str, Any]]:
        """Return the disks (``Item_Disk``) of one item.

        Args:
            items_id: Item id.
            **params: Extra API parameters (``range``...).

        Returns:
            The rows (empty list when there is none).
        """
        return cls.get_sub_items(items_id, "Item_Disk", **params)


class HasSimCards(CommonDBTM):
    """Adds ``get_sim_cards``."""

    @classmethod
    def get_sim_cards(cls, items_id: int, **params: Any) -> list[dict[str, Any]]:
        """Return the SIM cards installed (``Item_DeviceSimcard``) of one item.

        Args:
            items_id: Item id.
            **params: Extra API parameters (``range``...).

        Returns:
            The rows (empty list when there is none).
        """
        return cls.get_sub_items(items_id, "Item_DeviceSimcard", **params)


class HasRack(CommonDBTM):
    """Adds ``get_racks``."""

    @classmethod
    def get_racks(cls, items_id: int, **params: Any) -> list[dict[str, Any]]:
        """Return the rack positions (``Item_Rack``) of one item.

        Args:
            items_id: Item id.
            **params: Extra API parameters (``range``...).

        Returns:
            The rows (empty list when there is none).
        """
        return cls.get_sub_items(items_id, "Item_Rack", **params)


class HasRemoteManagement(CommonDBTM):
    """Adds ``get_remote_managements``."""

    @classmethod
    def get_remote_managements(cls, items_id: int, **params: Any) -> list[dict[str, Any]]:
        """Return the remote management entries (``Item_RemoteManagement``) of one item.

        Args:
            items_id: Item id.
            **params: Extra API parameters (``range``...).

        Returns:
            The rows (empty list when there is none).
        """
        return cls.get_sub_items(items_id, "Item_RemoteManagement", **params)


class HasReservation(CommonDBTM):
    """Adds ``get_reservation_items``."""

    @classmethod
    def get_reservation_items(cls, items_id: int, **params: Any) -> list[dict[str, Any]]:
        """Return the reservation records (``ReservationItem``) of one item.

        Args:
            items_id: Item id.
            **params: Extra API parameters (``range``...).

        Returns:
            The rows (empty list when there is none).
        """
        return cls.get_sub_items(items_id, "ReservationItem", **params)


class HasTickets(CommonDBTM):
    """Adds ``get_tickets``."""

    @classmethod
    def get_tickets(cls, items_id: int, **params: Any) -> list[dict[str, Any]]:
        """Return the ticket links (``Item_Ticket``) of one item.

        Args:
            items_id: Item id.
            **params: Extra API parameters (``range``...).

        Returns:
            The rows (empty list when there is none).
        """
        return cls.get_sub_items(items_id, "Item_Ticket", **params)


class HasNotes(CommonDBTM):
    """Adds ``get_notes``."""

    @classmethod
    def get_notes(cls, items_id: int, **params: Any) -> list[dict[str, Any]]:
        """Return the notes (``Notepad``) of one item.

        Args:
            items_id: Item id.
            **params: Extra API parameters (``range``...).

        Returns:
            The rows (empty list when there is none).
        """
        return cls.get_sub_items(items_id, "Notepad", **params)


class HasLogs(CommonDBTM):
    """Adds ``get_logs``."""

    @classmethod
    def get_logs(cls, items_id: int, **params: Any) -> list[dict[str, Any]]:
        """Return the history entries (``Log``) of one item.

        Args:
            items_id: Item id.
            **params: Extra API parameters (``range``...).

        Returns:
            The rows (empty list when there is none).
        """
        return cls.get_sub_items(items_id, "Log", **params)


class HasSoftware(CommonDBTM):
    """Adds ``get_software_versions`` and ``get_software_licenses``."""

    @classmethod
    def get_software_versions(cls, items_id: int, **params: Any) -> list[dict[str, Any]]:
        """Return the software versions installed on one item (``Item_SoftwareVersion``).

        Args:
            items_id: Item id.
            **params: Extra API parameters.

        Returns:
            The rows.
        """
        return cls.get_sub_items(items_id, "Item_SoftwareVersion", **params)

    @classmethod
    def get_software_licenses(cls, items_id: int, **params: Any) -> list[dict[str, Any]]:
        """Return the software licenses attached to one item (``Item_SoftwareLicense``).

        Args:
            items_id: Item id.
            **params: Extra API parameters.

        Returns:
            The rows.
        """
        return cls.get_sub_items(items_id, "Item_SoftwareLicense", **params)


class HasDevices(CommonDBTM):
    """Adds ``get_devices`` (components installed in the item)."""

    @classmethod
    def _device_itemtypes(cls) -> list[str]:
        """Return the ``Item_Device*`` itemtypes this class may own.

        Returns:
            The itemtypes, in GLPI order.
        """
        owner = cls._itemtype()
        return [name for name, owners in ITEM_DEVICE_TYPES.items() if owner in owners or "*" in owners]

    @classmethod
    def get_devices(cls, items_id: int, device_itemtype: str | None = None, **params: Any) -> list[dict[str, Any]]:
        """Return the components installed in one item.

        Args:
            items_id: Item id.
            device_itemtype: One ``Item_Device*`` itemtype (e.g. ``Item_DeviceProcessor``); ``None`` reads every
                kind this itemtype can own, one request each.
            **params: Extra API parameters (applied to each request).

        Returns:
            The rows. With ``device_itemtype=None`` each row gets the extra key ``device_itemtype``.

        Raises:
            ValueError: When ``device_itemtype`` is not an ``Item_Device*`` itemtype of GLPI 10.
            UnsupportedOperationError: When this itemtype cannot own that component kind.
        """
        allowed = cls._device_itemtypes()
        if device_itemtype is not None:
            if device_itemtype not in ITEM_DEVICE_TYPES:
                raise ValueError(f"unknown device itemtype: {device_itemtype!r}")
            if device_itemtype not in allowed:
                raise UnsupportedOperationError(f"{cls._itemtype()} cannot own {device_itemtype}")
            return cls.get_sub_items(items_id, device_itemtype, **params)
        rows: list[dict[str, Any]] = []
        for itemtype in allowed:
            # Copies: the key is added to new dicts, never to the connector rows
            rows.extend({**row, "device_itemtype": itemtype} for row in cls.get_sub_items(items_id, itemtype, **params))
        return rows
