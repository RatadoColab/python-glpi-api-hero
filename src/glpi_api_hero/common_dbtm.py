from glpi_api_hero import ApiCommunication

class CommonDBTM:
    
    @classmethod
    def get_class_name(cls) -> str:
        """Return the name of the class that called this method."""
        return cls.__name__

    @classmethod
    def add(cls, *items):
        return ApiCommunication.glpi.add(cls.__name__, *items)
    
    @classmethod
    def update(cls, *items):
        return ApiCommunication.glpi.update(cls.__name__, *items)
    
    @classmethod
    def delete(cls, *items, **kwargs):
        return ApiCommunication.glpi.delete(cls.__name__, *items, **kwargs)
    
    @classmethod
    def search(cls, **kwargs):
        return ApiCommunication.glpi.search(cls.__name__, **kwargs)
    
    @classmethod
    def get(cls, items_id, **kwargs):
        return ApiCommunication.glpi.get_item(cls.__name__, items_id, **kwargs)
    
    @classmethod
    def get_all_items(cls, **kwargs):
        return ApiCommunication.glpi.get_all_items(cls.__name__, **kwargs)

    @classmethod
    def get_sub_items(cls, items_id, sub_itemtype, **kwargs):
        return ApiCommunication.glpi.get_sub_items(cls.__name__, items_id, sub_itemtype, **kwargs)
    
    @classmethod
    def list_search_options(cls, items_id, raw=False):
        return ApiCommunication.glpi.list_search_options(cls.__name__, items_id, raw)
    
    @classmethod
    def field_id(cls, field_uid, refresh=False):
        return ApiCommunication.glpi.list_search_options(cls.__name__, field_uid, refresh)
    
    @classmethod
    def field_uid(cls, field_id, refresh=False):
        return ApiCommunication.glpi.list_search_options(cls.__name__, field_id, refresh)