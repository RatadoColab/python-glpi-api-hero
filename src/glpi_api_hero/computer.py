from glpi_api_hero.common_dbtm import CommonDBTM
from glpi_api_hero.api_communication import ApiCommunication


class Computer(CommonDBTM):

    # Métodos de busca ################################

    @classmethod
    def getByName(cls, name: str, **kwargs):
        """Busca computadores pelo nome.

        Args:
            name (str): Nome do computador no GLPI.
            **kwargs: Parâmetros extras repassados à busca.

        Returns:
            list: Lista de computadores encontrados.
        """
        criteria = [
            {
                'field': 1,
                'searchtype': 'contains',
                'value': name,
            }
        ]
        return ApiCommunication.glpi.search('Computer', criteria=criteria, **kwargs)

    @classmethod
    def getBySerial(cls, serial: str, **kwargs):
        """Busca computadores pelo número de série.

        Args:
            serial (str): Número de série do computador.
            **kwargs: Parâmetros extras repassados à busca.

        Returns:
            list: Lista de computadores encontrados.
        """
        criteria = [
            {
                'field': 5,
                'searchtype': 'equals',
                'value': serial,
            }
        ]
        return ApiCommunication.glpi.search('Computer', criteria=criteria, **kwargs)

    @classmethod
    def getByPatrimonio(cls, otherserial: str, **kwargs):
        """Busca computadores pelo número de patrimônio (otherserial).

        Args:
            otherserial (str): Número de patrimônio do computador.
            **kwargs: Parâmetros extras repassados à busca.

        Returns:
            list: Lista de computadores encontrados.
        """
        criteria = [
            {
                'field': 6,
                'searchtype': 'equals',
                'value': otherserial,
            }
        ]
        return ApiCommunication.glpi.search('Computer', criteria=criteria, **kwargs)

    # Métodos de sistema operacional ################################

    @classmethod
    def getOperatingSystem(cls, computer_id: int, **kwargs):
        """Retorna o sistema operacional instalado no computador.

        Args:
            computer_id (int): ID do computador no GLPI.
            **kwargs: Parâmetros extras repassados à chamada.

        Returns:
            list: Lista de registros de sistema operacional do computador.
        """
        return cls.get_sub_items(computer_id, 'Item_OperatingSystem', **kwargs)

    # Métodos de software ################################

    @classmethod
    def getSoftwares(cls, computer_id: int, **kwargs):
        """Retorna os softwares instalados no computador.

        Args:
            computer_id (int): ID do computador no GLPI.
            **kwargs: Parâmetros extras repassados à chamada.

        Returns:
            list: Lista de softwares instalados no computador.
        """
        return cls.get_sub_items(computer_id, 'Item_SoftwareVersion', **kwargs)

    # Métodos de rede ################################

    @classmethod
    def getNetworkPorts(cls, computer_id: int, **kwargs):
        """Retorna as portas de rede do computador.

        Args:
            computer_id (int): ID do computador no GLPI.
            **kwargs: Parâmetros extras repassados à chamada.

        Returns:
            list: Lista de portas de rede do computador.
        """
        return cls.get_sub_items(computer_id, 'NetworkPort', **kwargs)

    # Métodos de hardware ################################

    @classmethod
    def getProcessors(cls, computer_id: int, **kwargs):
        """Retorna os processadores do computador.

        Args:
            computer_id (int): ID do computador no GLPI.
            **kwargs: Parâmetros extras repassados à chamada.

        Returns:
            list: Lista de processadores do computador.
        """
        return cls.get_sub_items(computer_id, 'Item_DeviceProcessor', **kwargs)

    @classmethod
    def getMemories(cls, computer_id: int, **kwargs):
        """Retorna os módulos de memória RAM do computador.

        Args:
            computer_id (int): ID do computador no GLPI.
            **kwargs: Parâmetros extras repassados à chamada.

        Returns:
            list: Lista de módulos de memória do computador.
        """
        return cls.get_sub_items(computer_id, 'Item_DeviceMemory', **kwargs)

    @classmethod
    def getDisks(cls, computer_id: int, **kwargs):
        """Retorna os discos/volumes do computador.

        Args:
            computer_id (int): ID do computador no GLPI.
            **kwargs: Parâmetros extras repassados à chamada.

        Returns:
            list: Lista de discos/volumes do computador.
        """
        return cls.get_sub_items(computer_id, 'ComputerDisk', **kwargs)

    @classmethod
    def getHardDrives(cls, computer_id: int, **kwargs):
        """Retorna os discos rígidos/SSDs do computador.

        Args:
            computer_id (int): ID do computador no GLPI.
            **kwargs: Parâmetros extras repassados à chamada.

        Returns:
            list: Lista de discos rígidos do computador.
        """
        return cls.get_sub_items(computer_id, 'Item_DeviceHardDrive', **kwargs)

    # Métodos de máquinas virtuais ################################

    @classmethod
    def getVirtualMachines(cls, computer_id: int, **kwargs):
        """Retorna as máquinas virtuais hospedadas no computador.

        Args:
            computer_id (int): ID do computador (host) no GLPI.
            **kwargs: Parâmetros extras repassados à chamada.

        Returns:
            list: Lista de máquinas virtuais do computador.
        """
        return cls.get_sub_items(computer_id, 'ComputerVirtualMachine', **kwargs)

    # Métodos de chamados ################################

    @classmethod
    def getTickets(cls, computer_id: int, **kwargs):
        """Retorna os chamados vinculados ao computador.

        Args:
            computer_id (int): ID do computador no GLPI.
            **kwargs: Parâmetros extras repassados à busca.

        Returns:
            list: Lista de chamados vinculados ao computador.
        """
        criteria = [
            {
                'field': 131,
                'searchtype': 'equals',
                'value': computer_id,
            }
        ]
        return ApiCommunication.glpi.search('Ticket', criteria=criteria, **kwargs)

    # Métodos de informações de compra ################################

    @classmethod
    def getInfocom(cls, computer_id: int, **kwargs):
        """Retorna as informações financeiras e de garantia do computador.

        Args:
            computer_id (int): ID do computador no GLPI.
            **kwargs: Parâmetros extras repassados à chamada.

        Returns:
            list: Informações de compra e garantia do computador.
        """
        return cls.get_sub_items(computer_id, 'Infocom', **kwargs)

    # Métodos de logs ################################

    @classmethod
    def getLogs(cls, computer_id: int, **kwargs):
        """Retorna o histórico de alterações do computador.

        Args:
            computer_id (int): ID do computador no GLPI.
            **kwargs: Parâmetros extras repassados à chamada.

        Returns:
            list: Histórico de logs do computador.
        """
        return cls.get_sub_items(computer_id, 'Log', **kwargs)

