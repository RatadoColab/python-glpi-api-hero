"""Computers (GLPI ``Computer``)."""

from __future__ import annotations

from typing import Any

from glpi_api_hero.core.capabilities import (
    HasAppliances,
    HasCertificates,
    HasClusters,
    HasContracts,
    HasDevices,
    HasDisks,
    HasDocuments,
    HasDomains,
    HasInfocom,
    HasNetworkPorts,
    HasNotes,
    HasOperatingSystem,
    HasRack,
    HasRemoteManagement,
    HasReservation,
    HasSimCards,
    HasSoftware,
    HasTickets,
)
from glpi_api_hero.core.common_asset import CommonAsset


class Computer(
    CommonAsset,
    HasNotes,
    HasInfocom,
    HasNetworkPorts,
    HasContracts,
    HasDocuments,
    HasCertificates,
    HasDomains,
    HasAppliances,
    HasClusters,
    HasSoftware,
    HasOperatingSystem,
    HasDisks,
    HasDevices,
    HasSimCards,
    HasRack,
    HasRemoteManagement,
    HasReservation,
    HasTickets,
):
    """GLPI ``Computer`` (Assets > Computers)."""

    @classmethod
    def get_operating_system(cls, computer_id: int, **params: Any) -> list[dict[str, Any]]:
        """Return the operating system records (same request as ``get_operating_systems``).

        Args:
            computer_id: Computer id.
            **params: Extra API parameters.

        Returns:
            The ``Item_OperatingSystem`` rows.
        """
        return cls.get_operating_systems(computer_id, **params)

    @classmethod
    def get_softwares(cls, computer_id: int, **params: Any) -> list[dict[str, Any]]:
        """Return the installed software versions (same request as ``get_software_versions``).

        Args:
            computer_id: Computer id.
            **params: Extra API parameters.

        Returns:
            The ``Item_SoftwareVersion`` rows.
        """
        return cls.get_software_versions(computer_id, **params)

    @classmethod
    def get_processors(cls, computer_id: int, **params: Any) -> list[dict[str, Any]]:
        """Return the processors (``Item_DeviceProcessor``).

        Args:
            computer_id: Computer id.
            **params: Extra API parameters.

        Returns:
            The rows.
        """
        return cls.get_sub_items(computer_id, "Item_DeviceProcessor", **params)

    @classmethod
    def get_memories(cls, computer_id: int, **params: Any) -> list[dict[str, Any]]:
        """Return the memory modules (``Item_DeviceMemory``).

        Args:
            computer_id: Computer id.
            **params: Extra API parameters.

        Returns:
            The rows.
        """
        return cls.get_sub_items(computer_id, "Item_DeviceMemory", **params)

    @classmethod
    def get_hard_drives(cls, computer_id: int, **params: Any) -> list[dict[str, Any]]:
        """Return the hard drives (``Item_DeviceHardDrive``).

        Args:
            computer_id: Computer id.
            **params: Extra API parameters.

        Returns:
            The rows.
        """
        return cls.get_sub_items(computer_id, "Item_DeviceHardDrive", **params)

    @classmethod
    def get_virtual_machines(cls, computer_id: int, **params: Any) -> list[dict[str, Any]]:
        """Return the virtual machines hosted by the computer (``ComputerVirtualMachine``).

        Args:
            computer_id: Computer id.
            **params: Extra API parameters.

        Returns:
            The rows.
        """
        return cls.get_sub_items(computer_id, "ComputerVirtualMachine", **params)

    @classmethod
    def get_connections(cls, computer_id: int, **params: Any) -> list[dict[str, Any]]:
        """Return the monitors, peripherals, printers and phones plugged into the computer (``Computer_Item``).

        Args:
            computer_id: Computer id.
            **params: Extra API parameters.

        Returns:
            The link rows.
        """
        return cls.get_sub_items(computer_id, "Computer_Item", **params)
