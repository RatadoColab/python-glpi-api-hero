from glpi_api_hero.common_dbtm import CommonDBTM
from glpi_api_hero.api_communication import ApiCommunication
from glpi_api_hero.exceptions import ApiOperationError


class Location(CommonDBTM):

    # Métodos de busca ################################

    @classmethod
    def getByName(cls, name: str, **kwargs):
        """Busca localizações pelo nome.

        Args:
            name (str): Nome da localização no GLPI.
            **kwargs: Parâmetros extras repassados à busca.

        Returns:
            list: Lista de localizações encontradas.
        """
        criteria = [
            {
                'field': 1,
                'searchtype': 'contains',
                'value': name,
            }
        ]
        return ApiCommunication.glpi.search('Location', criteria=criteria, **kwargs)

    @classmethod
    def getByCode(cls, code, **kwargs):
        """Busca uma localização pelo código externo (campo code).

        Args:
            code: Valor do campo code no GLPI.
            **kwargs: Parâmetros extras repassados à busca.

        Returns:
            dict: Resultado da busca retornado pela API.
        """
        criteria = [
            {
                'field': 11,
                'searchtype': 'equals',
                'value': code,
            }
        ]
        return ApiCommunication.glpi.search('Location', criteria=criteria, **kwargs)

    @classmethod
    def getByCompleteName(cls, complete_name: str, **kwargs):
        """Busca localizações pelo nome completo (caminho hierárquico).

        Args:
            complete_name (str): Nome completo da localização (ex: 'Sede > Bloco A > Sala 101').
            **kwargs: Parâmetros extras repassados à busca.

        Returns:
            list: Lista de localizações encontradas.
        """
        criteria = [
            {
                'field': 2,
                'searchtype': 'contains',
                'value': complete_name,
            }
        ]
        return ApiCommunication.glpi.search('Location', criteria=criteria, **kwargs)

    # Métodos de hierarquia ################################

    @classmethod
    def getChildren(cls, location_id: int, **kwargs):
        """Retorna as sub-localizações filhas diretas de uma localização.

        Args:
            location_id (int): ID da localização pai no GLPI.
            **kwargs: Parâmetros extras repassados à busca.

        Returns:
            list: Lista de localizações filhas.
        """
        criteria = [
            {
                'field': 13,
                'searchtype': 'equals',
                'value': location_id,
            }
        ]
        return ApiCommunication.glpi.search('Location', criteria=criteria, **kwargs)

    @classmethod
    def getRoots(cls, **kwargs):
        """Retorna todas as localizações raiz (sem localização pai).

        Args:
            **kwargs: Parâmetros extras repassados à busca.

        Returns:
            list: Lista de localizações raiz.
        """
        criteria = [
            {
                'field': 13,
                'searchtype': 'equals',
                'value': 0,
            }
        ]
        return ApiCommunication.glpi.search('Location', criteria=criteria, **kwargs)

    # Métodos de itens na localização ################################

    @classmethod
    def getComputers(cls, location_id: int, **kwargs):
        """Retorna os computadores associados à localização.

        Args:
            location_id (int): ID da localização no GLPI.
            **kwargs: Parâmetros extras repassados à busca.

        Returns:
            list: Lista de computadores na localização.
        """
        criteria = [
            {
                'field': 3,
                'searchtype': 'equals',
                'value': location_id,
            }
        ]
        return ApiCommunication.glpi.search('Computer', criteria=criteria, **kwargs)

    @classmethod
    def getNetworkEquipments(cls, location_id: int, **kwargs):
        """Retorna os equipamentos de rede associados à localização.

        Args:
            location_id (int): ID da localização no GLPI.
            **kwargs: Parâmetros extras repassados à busca.

        Returns:
            list: Lista de equipamentos de rede na localização.
        """
        criteria = [
            {
                'field': 3,
                'searchtype': 'equals',
                'value': location_id,
            }
        ]
        return ApiCommunication.glpi.search('NetworkEquipment', criteria=criteria, **kwargs)

    @classmethod
    def getTickets(cls, location_id: int, **kwargs):
        """Retorna os chamados associados à localização.

        Args:
            location_id (int): ID da localização no GLPI.
            **kwargs: Parâmetros extras repassados à busca.

        Returns:
            list: Lista de chamados na localização.
        """
        criteria = [
            {
                'field': 83,
                'searchtype': 'equals',
                'value': location_id,
            }
        ]
        return ApiCommunication.glpi.search('Ticket', criteria=criteria, **kwargs)

    @classmethod
    def getUsers(cls, location_id: int, **kwargs):
        """Retorna os usuários associados à localização.

        Args:
            location_id (int): ID da localização no GLPI.
            **kwargs: Parâmetros extras repassados à busca.

        Returns:
            list: Lista de usuários na localização.
        """
        criteria = [
            {
                'field': 5,
                'searchtype': 'equals',
                'value': location_id,
            }
        ]
        return ApiCommunication.glpi.search('User', criteria=criteria, **kwargs)

    # Métodos de criação ################################

    @classmethod
    def addFromList(cls, items: list, locations_id: int = 0, entities_id: int = 0,
                    *, mapper=None):
        """Create multiple locations from a list of records.

        Args:
            items (list): Records to create. Each one is either a dict already holding
                GLPI Location fields or, when mapper is given, a record in any source format.
            locations_id (int): Parent location ID in GLPI. Default: 0 (root).
            entities_id (int): Entity ID in GLPI. Default: 0 (root entity).
            mapper (callable, optional): Function receiving one record and returning a dict
                of GLPI Location fields. Default: records are used as they are.

        Returns:
            list: Operation result returned by the API.
        """
        # Apply the mapper (when provided) and attach parent location and entity
        mapped_items = [
            {**(mapper(item) if mapper else dict(item)),
             'locations_id': locations_id, 'entities_id': entities_id}
            for item in items
        ]
        return cls.add(*mapped_items)

    @classmethod
    def updateFromList(cls, items: list, locations_id: int = 0, entities_id: int = 0,
                       *, mapper=None, key_field: str = 'code'):
        """Update existing locations from a list of records, creating the missing ones.

        An existing location is matched by key_field first and by name as a fallback;
        when no match is found a new location is created.

        Args:
            items (list): Records to process (see addFromList).
            locations_id (int): Parent location ID for new entries. Default: 0.
            entities_id (int): Entity ID for new entries. Default: 0.
            mapper (callable, optional): Function converting one record into a dict of
                GLPI Location fields. Default: records are used as they are.
            key_field (str): GLPI field used as unique key to match existing locations.
                Default: 'code'.

        Returns:
            list: Operation results (one entry per processed item).
        """
        # get_all_items returns full objects with a direct 'id' — no field ID ambiguity
        all_locations = cls.get_all_items(range='0-9999')
        if not isinstance(all_locations, list):
            all_locations = []

        if not all_locations:
            print(
                '[AVISO] get_all_items retornou 0 localizações. '
                'Verifique se o perfil GLPI tem permissão de LEITURA em Location '
                '(Setup > Profiles > seu perfil > Assets > Locations: Read).'
            )

        # Index current locations by key and by name for matching
        by_key  = {str(loc[key_field]): loc for loc in all_locations if loc.get(key_field)}
        by_name = {loc['name']: loc         for loc in all_locations if loc.get('name')}

        results = []
        for item in items:
            mapped = mapper(item) if mapper else dict(item)
            key    = mapped.get(key_field)
            name   = mapped.get('name', '')

            # Match by key first, then by name
            existing = by_key.get(str(key)) if key else None
            if not existing:
                existing = by_name.get(name)

            if existing:
                results.append(cls.update({**mapped, 'id': existing['id']}))
            else:
                try:
                    results.append(cls.add(
                        {**mapped, 'locations_id': locations_id, 'entities_id': entities_id}
                    ))
                except ApiOperationError as exc:
                    if 'Duplicate entry' in str(exc):
                        print(
                            f'[AVISO] "{name}" já existe no GLPI mas não foi encontrada via API. '
                            'Corrija a permissão de leitura para habilitar a atualização.'
                        )
                        results.append({'skipped': True, 'name': name})
                    else:
                        raise
        return results

    # Métodos de logs ################################

    @classmethod
    def getLogs(cls, location_id: int, **kwargs):
        """Retorna o histórico de alterações da localização.

        Args:
            location_id (int): ID da localização no GLPI.
            **kwargs: Parâmetros extras repassados à chamada.

        Returns:
            list: Histórico de logs da localização.
        """
        return cls.get_sub_items(location_id, 'Log', **kwargs)
