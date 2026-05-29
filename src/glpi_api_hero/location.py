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
        """Busca uma localização pelo código (COD_SIORG), usado como chave primária.

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
    def _dms_to_decimal(cls, graus: int, minutos: int, segundos: float) -> float:
        """Converte coordenadas de graus/minutos/segundos para decimal."""
        return graus + minutos / 60 + segundos / 3600

    @classmethod
    def _map_sda(cls, item: dict) -> dict:
        """Converte um dicionário de unidade organizacional do SDA para campos do GLPI Location.

        Campos com mapeamento direto:
            NOME        → name
            COD_SIORG   → code
            ENDERECO    → address
            COMPLEMENTO → address  (concatenado ao ENDERECO quando presente)
            BAIRRO      → building
            CEP         → postcode
            CIDADE      → town
            UF          → state
            coordenadas → latitude / longitude (graus decimais, sul/oeste negativos)

        Campos sem equivalente GLPI (agrupados em comment):
            SIGLA, NORMATIVO_VIGENTE, TELEFONES, TITULA, SUBSTITUTO

        Args:
            item (dict): Dicionário de unidade organizacional do SDA.

        Returns:
            dict: Dicionário com campos do GLPI (sem locations_id / entities_id).
        """
        address = item.get('ENDERECO') or ''
        complement = item.get('COMPLEMENTO')
        if complement:
            address = f'{address}, {complement}'

        comment_parts = []
        for label, key in [
            ('Sigla', 'SIGLA'),
            ('Normativo vigente', 'NORMATIVO_VIGENTE'),
            ('Telefones', 'TELEFONES'),
            ('Titular (ID)', 'TITULA'),
            ('Substituto (ID)', 'SUBSTITUTO'),
        ]:
            value = item.get(key)
            if value is not None:
                comment_parts.append(f'{label}: {value}')

        lat = cls._dms_to_decimal(
            item.get('LAT_GRAUS', 0),
            item.get('LAT_MINUTOS', 0),
            item.get('LAT_SEGUNDOS', 0.0),
        )
        lon = cls._dms_to_decimal(
            item.get('LON_GRAUS', 0),
            item.get('LON_MINUTOS', 0),
            item.get('LON_SEGUNDOS', 0.0),
        )

        mapped = {
            'name':      item.get('NOME', ''),
            'code':      item.get('COD_SIORG'),
            'comment':   ' | '.join(comment_parts),
            'address':   address,
            'building':  item.get('BAIRRO', ''),
            'postcode':  item.get('CEP', ''),
            'town':      item.get('CIDADE', ''),
            'state':     item.get('UF', ''),
            'latitude':  str(round(-lat, 6)),
            'longitude': str(round(-lon, 6)),
        }
        return {k: v for k, v in mapped.items() if v not in ('', None)}

    @classmethod
    def addFromList(cls, items: list, locations_id: int = 0, entities_id: int = 0):
        """Cria múltiplas localizações a partir de uma lista de unidades organizacionais do SDA.

        Args:
            items (list): Lista de dicionários de unidades organizacionais do SDA.
            locations_id (int): ID da localização pai no GLPI. Padrão: 0 (raiz).
            entities_id (int): ID da entidade no GLPI. Padrão: 0 (entidade raiz).

        Returns:
            list: Resultado da operação retornado pela API.
        """
        mapped_items = [
            {**cls._map_sda(item), 'locations_id': locations_id, 'entities_id': entities_id}
            for item in items
        ]
        return cls.add(*mapped_items)

    @classmethod
    def updateFromList(cls, items: list, locations_id: int = 0, entities_id: int = 0):
        """Atualiza localizações existentes a partir de uma lista de unidades organizacionais do SDA.

        Usa COD_SIORG (campo code) como chave primária para decidir entre
        atualizar uma localização existente ou criar uma nova.

        Args:
            items (list): Lista de dicionários de unidades organizacionais do SDA.
            locations_id (int): ID da localização pai para novas entradas. Padrão: 0.
            entities_id (int): ID da entidade para novas entradas. Padrão: 0.

        Returns:
            list: Resultados das operações (uma entrada por item processado).
        """
        # get_all_items retorna objetos completos com 'id' direto — sem ambiguidade de field IDs
        all_locations = cls.get_all_items(range='0-9999')
        if not isinstance(all_locations, list):
            all_locations = []

        if not all_locations:
            print(
                '[AVISO] get_all_items retornou 0 localizações. '
                'Verifique se o perfil GLPI tem permissão de LEITURA em Location '
                '(Setup > Profiles > seu perfil > Assets > Locations: Read).'
            )

        by_code = {str(loc['code']): loc for loc in all_locations if loc.get('code')}
        by_name = {loc['name']: loc          for loc in all_locations if loc.get('name')}

        results = []
        for item in items:
            mapped    = cls._map_sda(item)
            cod_siorg = mapped.get('code')
            name      = mapped.get('name', '')

            existing = by_code.get(str(cod_siorg)) if cod_siorg else None
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
