from typing import Any

from glpi_api_hero.assistance.ticket import Ticket
from glpi_api_hero.core.common_dbtm import CommonDBTM


class Computer(CommonDBTM):
    """Computers (Assets > Computers)."""

    # Search option ids of the Computer itemtype (GLPI 10 rawSearchOptions)
    SEARCH_FIELD_NAME = 1
    SEARCH_FIELD_SERIAL = 5
    SEARCH_FIELD_INVENTORY_NUMBER = 6
    SEARCH_FIELD_LOCATION = 3

    # Métodos de busca ################################

    @classmethod
    def get_by_name(cls, name: str, **kwargs: Any) -> list[dict[str, Any]]:
        """Busca computadores pelo nome.

        Args:
            name (str): Nome do computador no GLPI.
            **kwargs: Parâmetros extras repassados à busca.

        Returns:
            list: Lista de computadores encontrados.
        """
        criteria = [
            {
                "field": cls.SEARCH_FIELD_NAME,
                "searchtype": "contains",
                "value": name,
            }
        ]
        return cls.search(criteria, **kwargs)

    @classmethod
    def get_by_serial(cls, serial: str, **kwargs: Any) -> list[dict[str, Any]]:
        """Busca computadores pelo número de série.

        Args:
            serial (str): Número de série do computador.
            **kwargs: Parâmetros extras repassados à busca.

        Returns:
            list: Lista de computadores encontrados.
        """
        criteria = [
            {
                "field": cls.SEARCH_FIELD_SERIAL,
                "searchtype": "equals",
                "value": serial,
            }
        ]
        return cls.search(criteria, **kwargs)

    @classmethod
    def get_by_inventory_number(cls, otherserial: str, **kwargs: Any) -> list[dict[str, Any]]:
        """Busca computadores pelo número de patrimônio (otherserial).

        Args:
            otherserial (str): Número de patrimônio do computador.
            **kwargs: Parâmetros extras repassados à busca.

        Returns:
            list: Lista de computadores encontrados.
        """
        criteria = [
            {
                "field": cls.SEARCH_FIELD_INVENTORY_NUMBER,
                "searchtype": "equals",
                "value": otherserial,
            }
        ]
        return cls.search(criteria, **kwargs)

    # Métodos de sistema operacional ################################

    @classmethod
    def get_operating_system(cls, computer_id: int, **kwargs: Any) -> list[dict[str, Any]]:
        """Retorna o sistema operacional instalado no computador.

        Args:
            computer_id (int): ID do computador no GLPI.
            **kwargs: Parâmetros extras repassados à chamada.

        Returns:
            list: Lista de registros de sistema operacional do computador.
        """
        return cls.get_sub_items(computer_id, "Item_OperatingSystem", **kwargs)

    # Métodos de software ################################

    @classmethod
    def get_softwares(cls, computer_id: int, **kwargs: Any) -> list[dict[str, Any]]:
        """Retorna os softwares instalados no computador.

        Args:
            computer_id (int): ID do computador no GLPI.
            **kwargs: Parâmetros extras repassados à chamada.

        Returns:
            list: Lista de softwares instalados no computador.
        """
        return cls.get_sub_items(computer_id, "Item_SoftwareVersion", **kwargs)

    # Métodos de rede ################################

    @classmethod
    def get_network_ports(cls, computer_id: int, **kwargs: Any) -> list[dict[str, Any]]:
        """Retorna as portas de rede do computador.

        Args:
            computer_id (int): ID do computador no GLPI.
            **kwargs: Parâmetros extras repassados à chamada.

        Returns:
            list: Lista de portas de rede do computador.
        """
        return cls.get_sub_items(computer_id, "NetworkPort", **kwargs)

    # Métodos de hardware ################################

    @classmethod
    def get_processors(cls, computer_id: int, **kwargs: Any) -> list[dict[str, Any]]:
        """Retorna os processadores do computador.

        Args:
            computer_id (int): ID do computador no GLPI.
            **kwargs: Parâmetros extras repassados à chamada.

        Returns:
            list: Lista de processadores do computador.
        """
        return cls.get_sub_items(computer_id, "Item_DeviceProcessor", **kwargs)

    @classmethod
    def get_memories(cls, computer_id: int, **kwargs: Any) -> list[dict[str, Any]]:
        """Retorna os módulos de memória RAM do computador.

        Args:
            computer_id (int): ID do computador no GLPI.
            **kwargs: Parâmetros extras repassados à chamada.

        Returns:
            list: Lista de módulos de memória do computador.
        """
        return cls.get_sub_items(computer_id, "Item_DeviceMemory", **kwargs)

    @classmethod
    def get_disks(cls, computer_id: int, **kwargs: Any) -> list[dict[str, Any]]:
        """Retorna os discos/volumes do computador.

        Args:
            computer_id (int): ID do computador no GLPI.
            **kwargs: Parâmetros extras repassados à chamada.

        Returns:
            list: Lista de discos/volumes do computador.
        """
        return cls.get_sub_items(computer_id, "Item_Disk", **kwargs)

    @classmethod
    def get_hard_drives(cls, computer_id: int, **kwargs: Any) -> list[dict[str, Any]]:
        """Retorna os discos rígidos/SSDs do computador.

        Args:
            computer_id (int): ID do computador no GLPI.
            **kwargs: Parâmetros extras repassados à chamada.

        Returns:
            list: Lista de discos rígidos do computador.
        """
        return cls.get_sub_items(computer_id, "Item_DeviceHardDrive", **kwargs)

    # Métodos de máquinas virtuais ################################

    @classmethod
    def get_virtual_machines(cls, computer_id: int, **kwargs: Any) -> list[dict[str, Any]]:
        """Retorna as máquinas virtuais hospedadas no computador.

        Args:
            computer_id (int): ID do computador (host) no GLPI.
            **kwargs: Parâmetros extras repassados à chamada.

        Returns:
            list: Lista de máquinas virtuais do computador.
        """
        return cls.get_sub_items(computer_id, "ComputerVirtualMachine", **kwargs)

    # Métodos de chamados ################################

    @classmethod
    def get_tickets(cls, computer_id: int, **kwargs: Any) -> list[dict[str, Any]]:
        """Retorna os chamados vinculados ao computador.

        Args:
            computer_id (int): ID do computador no GLPI.
            **kwargs: Parâmetros extras repassados à busca.

        Returns:
            list: Lista de chamados vinculados ao computador.
        """
        criteria = [
            {
                "field": Ticket.SEARCH_FIELD_ITEM_TYPE,
                "searchtype": "equals",
                "value": computer_id,
            }
        ]
        return Ticket.search(criteria, **kwargs)

    # Métodos de informações de compra ################################

    @classmethod
    def get_infocom(cls, computer_id: int, **kwargs: Any) -> list[dict[str, Any]]:
        """Retorna as informações financeiras e de garantia do computador.

        Args:
            computer_id (int): ID do computador no GLPI.
            **kwargs: Parâmetros extras repassados à chamada.

        Returns:
            list: Informações de compra e garantia do computador.
        """
        return cls.get_sub_items(computer_id, "Infocom", **kwargs)

    # Métodos de logs ################################

    @classmethod
    def get_logs(cls, computer_id: int, **kwargs: Any) -> list[dict[str, Any]]:
        """Retorna o histórico de alterações do computador.

        Args:
            computer_id (int): ID do computador no GLPI.
            **kwargs: Parâmetros extras repassados à chamada.

        Returns:
            list: Histórico de logs do computador.
        """
        return cls.get_sub_items(computer_id, "Log", **kwargs)
