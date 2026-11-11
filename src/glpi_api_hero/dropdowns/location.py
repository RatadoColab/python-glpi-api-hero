import logging
from collections.abc import Callable
from typing import Any

from glpi_api_hero.administration.user import User
from glpi_api_hero.assets.computer import Computer
from glpi_api_hero.assets.network_equipment import NetworkEquipment
from glpi_api_hero.assistance.ticket import Ticket
from glpi_api_hero.core.common_dbtm import CommonDBTM
from glpi_api_hero.exceptions import GlpiAPIError

logger = logging.getLogger("glpi_api_hero")


class Location(CommonDBTM):
    """Locations (Setup > Dropdowns > Locations)."""

    # Search option ids of the Location itemtype (GLPI 10 rawSearchOptions)
    SEARCH_FIELD_COMPLETE_NAME = 1
    SEARCH_FIELD_NAME = 14
    SEARCH_FIELD_PARENT = 13
    # "code" is not a core GLPI field: option 11 is the building number; the field of the
    # deployment (e.g. a plugin option) must be set by the application
    SEARCH_FIELD_CODE = 11

    # Métodos de busca ################################

    @classmethod
    def get_by_name(cls, name: str, **kwargs: Any) -> list[dict[str, Any]]:
        """Busca localizações pelo nome.

        Args:
            name (str): Nome da localização no GLPI.
            **kwargs: Parâmetros extras repassados à busca.

        Returns:
            list: Lista de localizações encontradas.
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
    def get_by_code(cls, code: str, **kwargs: Any) -> list[dict[str, Any]]:
        """Busca uma localização pelo código externo (campo code).

        Args:
            code: Valor do campo code no GLPI.
            **kwargs: Parâmetros extras repassados à busca.

        Returns:
            dict: Resultado da busca retornado pela API.
        """
        criteria = [
            {
                "field": cls.SEARCH_FIELD_CODE,
                "searchtype": "equals",
                "value": code,
            }
        ]
        return cls.search(criteria, **kwargs)

    @classmethod
    def get_by_complete_name(cls, complete_name: str, **kwargs: Any) -> list[dict[str, Any]]:
        """Busca localizações pelo nome completo (caminho hierárquico).

        Args:
            complete_name (str): Nome completo da localização (ex: 'Sede > Bloco A > Sala 101').
            **kwargs: Parâmetros extras repassados à busca.

        Returns:
            list: Lista de localizações encontradas.
        """
        criteria = [
            {
                "field": cls.SEARCH_FIELD_COMPLETE_NAME,
                "searchtype": "contains",
                "value": complete_name,
            }
        ]
        return cls.search(criteria, **kwargs)

    # Métodos de hierarquia ################################

    @classmethod
    def get_children(cls, location_id: int, **kwargs: Any) -> list[dict[str, Any]]:
        """Retorna as sub-localizações filhas diretas de uma localização.

        Args:
            location_id (int): ID da localização pai no GLPI.
            **kwargs: Parâmetros extras repassados à busca.

        Returns:
            list: Lista de localizações filhas.
        """
        criteria = [
            {
                "field": cls.SEARCH_FIELD_PARENT,
                "searchtype": "equals",
                "value": location_id,
            }
        ]
        return cls.search(criteria, **kwargs)

    @classmethod
    def get_roots(cls, **kwargs: Any) -> list[dict[str, Any]]:
        """Retorna todas as localizações raiz (sem localização pai).

        Args:
            **kwargs: Parâmetros extras repassados à busca.

        Returns:
            list: Lista de localizações raiz.
        """
        criteria = [
            {
                "field": cls.SEARCH_FIELD_PARENT,
                "searchtype": "equals",
                "value": 0,
            }
        ]
        return cls.search(criteria, **kwargs)

    # Métodos de itens na localização ################################

    @classmethod
    def get_computers(cls, location_id: int, **kwargs: Any) -> list[dict[str, Any]]:
        """Retorna os computadores associados à localização.

        Args:
            location_id (int): ID da localização no GLPI.
            **kwargs: Parâmetros extras repassados à busca.

        Returns:
            list: Lista de computadores na localização.
        """
        criteria = [
            {
                "field": Computer.SEARCH_FIELD_LOCATION,
                "searchtype": "equals",
                "value": location_id,
            }
        ]
        return Computer.search(criteria, **kwargs)

    @classmethod
    def get_network_equipments(cls, location_id: int, **kwargs: Any) -> list[dict[str, Any]]:
        """Retorna os equipamentos de rede associados à localização.

        Args:
            location_id (int): ID da localização no GLPI.
            **kwargs: Parâmetros extras repassados à busca.

        Returns:
            list: Lista de equipamentos de rede na localização.
        """
        criteria = [
            {
                "field": NetworkEquipment.SEARCH_FIELD_LOCATION,
                "searchtype": "equals",
                "value": location_id,
            }
        ]
        return NetworkEquipment.search(criteria, **kwargs)

    @classmethod
    def get_tickets(cls, location_id: int, **kwargs: Any) -> list[dict[str, Any]]:
        """Retorna os chamados associados à localização.

        Args:
            location_id (int): ID da localização no GLPI.
            **kwargs: Parâmetros extras repassados à busca.

        Returns:
            list: Lista de chamados na localização.
        """
        criteria = [
            {
                "field": Ticket.SEARCH_FIELD_LOCATION,
                "searchtype": "equals",
                "value": location_id,
            }
        ]
        return Ticket.search(criteria, **kwargs)

    @classmethod
    def get_users(cls, location_id: int, **kwargs: Any) -> list[dict[str, Any]]:
        """Retorna os usuários associados à localização.

        Args:
            location_id (int): ID da localização no GLPI.
            **kwargs: Parâmetros extras repassados à busca.

        Returns:
            list: Lista de usuários na localização.
        """
        criteria = [
            {
                "field": User.SEARCH_FIELD_LOCATION,
                "searchtype": "equals",
                "value": location_id,
            }
        ]
        return User.search(criteria, **kwargs)

    # Métodos de criação ################################

    @classmethod
    def add_from_list(
        cls,
        items: list[Any],
        locations_id: int = 0,
        entities_id: int = 0,
        *,
        mapper: Callable[[Any], dict[str, Any]] | None = None,
    ) -> list[int]:
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
            {"locations_id": locations_id, "entities_id": entities_id, **(mapper(item) if mapper else dict(item))}
            for item in items
        ]
        return cls.add_many(mapped_items)

    @classmethod
    def update_from_list(
        cls,
        items: list[Any],
        locations_id: int = 0,
        entities_id: int = 0,
        *,
        mapper: Callable[[Any], dict[str, Any]] | None = None,
        key_field: str = "code",
    ) -> list[Any]:
        """Update existing locations from a list of records, creating the missing ones.

        An existing location is matched by key_field first and by name as a fallback;
        when no match is found a new location is created.

        Args:
            items (list): Records to process (see add_from_list).
            locations_id (int): Parent location ID for new entries. Default: 0.
            entities_id (int): Entity ID for new entries. Default: 0.
            mapper (callable, optional): Function converting one record into a dict of
                GLPI Location fields. Default: records are used as they are.
            key_field (str): GLPI field used as unique key to match existing locations.
                Default: 'code'.

        Returns:
            list: Operation results (one entry per processed item).
        """
        # Nothing to process: no request is needed
        if not items:
            return []

        # get_all returns full objects with a direct 'id' — no field ID ambiguity
        all_locations = cls.get_all(range="0-9999")
        if not isinstance(all_locations, list):
            all_locations = []

        if not all_locations:
            logger.warning(
                "get_all returned no Location: check that the GLPI profile can read Locations "
                "(Setup > Profiles > Assets > Locations: Read)"
            )

        # Index current locations by key and by name for matching
        by_key = {str(loc[key_field]): loc for loc in all_locations if loc.get(key_field)}
        by_name = {loc["name"]: loc for loc in all_locations if loc.get("name")}

        results = []
        for item in items:
            mapped = mapper(item) if mapper else dict(item)
            key = mapped.get(key_field)
            name = mapped.get("name", "")

            # Match by key first, then by name
            existing = by_key.get(str(key)) if key else None
            if not existing:
                existing = by_name.get(name)

            if existing:
                results.append(cls.update(existing["id"], mapped))
            else:
                try:
                    results.append(cls.add({"locations_id": locations_id, "entities_id": entities_id, **mapped}))
                except GlpiAPIError as exc:
                    if "Duplicate entry" in str(exc):
                        logger.warning(
                            "Location %r already exists but was not found through the API: "
                            "fix the read permission to enable updates",
                            name,
                        )
                        results.append({"skipped": True, "name": name})
                    else:
                        raise
        return results

    # Métodos de logs ################################

    @classmethod
    def get_logs(cls, location_id: int, **kwargs: Any) -> list[dict[str, Any]]:
        """Retorna o histórico de alterações da localização.

        Args:
            location_id (int): ID da localização no GLPI.
            **kwargs: Parâmetros extras repassados à chamada.

        Returns:
            list: Histórico de logs da localização.
        """
        return cls.get_sub_items(location_id, "Log", **kwargs)
