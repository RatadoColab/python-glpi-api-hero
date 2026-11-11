"""Example mapper: converts an organizational-unit record into GLPI Location fields.

Usage with the library:

    from glpi_api_hero.dropdowns import Location
    from examples.org_units.mapper import map_org_unit

    Location.update_from_list(units, mapper=map_org_unit, key_field='code')
"""


def dms_to_decimal(degrees: int, minutes: int, seconds: float) -> float:
    """Convert coordinates from degrees/minutes/seconds to decimal degrees."""
    return degrees + minutes / 60 + seconds / 3600


def map_org_unit(item: dict) -> dict:
    """Convert an organizational-unit dictionary into GLPI Location fields.

    Directly mapped fields:
        NOME        -> name
        COD_UNIDADE -> code
        ENDERECO    -> address
        COMPLEMENTO -> address  (appended to ENDERECO when present)
        BAIRRO      -> building
        CEP         -> postcode
        CIDADE      -> town
        UF          -> state
        coordinates -> latitude / longitude (decimal degrees, assumed south/west)

    Fields without a GLPI equivalent are grouped into comment:
        SIGLA, NORMATIVO_VIGENTE, TELEFONES, TITULA, SUBSTITUTO

    Args:
        item (dict): Organizational-unit record in the source format.

    Returns:
        dict: GLPI fields (without locations_id / entities_id).
    """
    address = item.get('ENDERECO') or ''
    complement = item.get('COMPLEMENTO')
    if complement:
        address = f'{address}, {complement}'

    # Collect fields that have no direct GLPI column into a single comment
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

    lat = dms_to_decimal(
        item.get('LAT_GRAUS', 0),
        item.get('LAT_MINUTOS', 0),
        item.get('LAT_SEGUNDOS', 0.0),
    )
    lon = dms_to_decimal(
        item.get('LON_GRAUS', 0),
        item.get('LON_MINUTOS', 0),
        item.get('LON_SEGUNDOS', 0.0),
    )

    mapped = {
        'name':      item.get('NOME', ''),
        'code':      item.get('COD_UNIDADE'),
        'comment':   ' | '.join(comment_parts),
        'address':   address,
        'building':  item.get('BAIRRO', ''),
        'postcode':  item.get('CEP', ''),
        'town':      item.get('CIDADE', ''),
        'state':     item.get('UF', ''),
        'latitude':  str(round(-lat, 6)),
        'longitude': str(round(-lon, 6)),
    }
    # Drop empty values so they do not overwrite existing GLPI data
    return {k: v for k, v in mapped.items() if v not in ('', None)}
