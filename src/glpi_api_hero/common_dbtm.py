from glpi_api_hero import ApiCommunication

class CommonDBTM:

    # Subclasses definem _glpi_name quando o nome Python diverge do itemtype do GLPI.
    _glpi_name: str = None

    @classmethod
    def _itemtype(cls) -> str:
        return cls._glpi_name if cls._glpi_name else cls.__name__

    @classmethod
    def get_class_name(cls) -> str:
        """Return the GLPI itemtype name used in API calls."""
        return cls._itemtype()

    @classmethod
    def add(cls, *items):
        return ApiCommunication.glpi.add(cls._itemtype(), *items)

    @classmethod
    def update(cls, *items):
        return ApiCommunication.glpi.update(cls._itemtype(), *items)

    @classmethod
    def delete(cls, *items, **kwargs):
        return ApiCommunication.glpi.delete(cls._itemtype(), *items, **kwargs)

    @classmethod
    def search(cls, **kwargs):
        return ApiCommunication.glpi.search(cls._itemtype(), **kwargs)

    @classmethod
    def get(cls, items_id, **kwargs):
        return ApiCommunication.glpi.get_item(cls._itemtype(), items_id, **kwargs)

    @classmethod
    def get_all_items(cls, **kwargs):
        return ApiCommunication.glpi.get_all_items(cls._itemtype(), **kwargs)

    @classmethod
    def get_sub_items(cls, items_id, sub_itemtype, **kwargs):
        return ApiCommunication.glpi.get_sub_items(cls._itemtype(), items_id, sub_itemtype, **kwargs)

    @classmethod
    def list_search_options(cls, items_id, raw=False):
        return ApiCommunication.glpi.list_search_options(cls._itemtype(), items_id, raw)

    @classmethod
    def field_id(cls, field_uid, refresh=False):
        return ApiCommunication.glpi.list_search_options(cls._itemtype(), field_uid, refresh)

    @classmethod
    def field_uid(cls, field_id, refresh=False):
        return ApiCommunication.glpi.list_search_options(cls._itemtype(), field_id, refresh)
