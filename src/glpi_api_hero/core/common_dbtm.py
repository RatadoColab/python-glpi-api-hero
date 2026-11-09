"""Generic CRUD shared by every GLPI itemtype.

Every method is a class method: models are never instantiated. Return values are
normalized and independent of the API version (see :mod:`glpi_api_hero.core.connector`).

Example::

    from glpi_api_hero import Glpi
    from glpi_api_hero.location import Location

    with Glpi.session(url, app_token, user_token=token):
        loc_id = Location.add({"name": "Room 101", "entities_id": 0})   # -> 42
        Location.update(loc_id, {"comment": "2nd floor"})              # -> None
"""

from __future__ import annotations

import functools
from collections.abc import Callable, Sequence
from typing import Any, ClassVar

from glpi_api_hero.core.connector import Connector
from glpi_api_hero.core.session import Glpi
from glpi_api_hero.core.types import OperationResult
from glpi_api_hero.exceptions import BadRequestError, PartialOperationError


class CommonDBTM:
    """Base class of the GLPI itemtype models.

    Attributes:
        _glpi_name: GLPI itemtype, when it differs from the Python class name.
    """

    _glpi_name: ClassVar[str | None] = None

    @classmethod
    def _itemtype(cls) -> str:
        """Return the GLPI itemtype of the class.

        Returns:
            ``_glpi_name`` when set, otherwise the class name.
        """
        return cls._glpi_name if cls._glpi_name else cls.__name__

    @classmethod
    def _connector(cls) -> Connector:
        """Return the connector of the global session.

        Returns:
            The active connector.

        Raises:
            ConfigurationError: When no session is open.
        """
        return Glpi.connector()

    @classmethod
    def get_class_name(cls) -> str:
        """Return the GLPI itemtype used in API calls.

        Returns:
            The itemtype.
        """
        return cls._itemtype()

    # -------------------------------------------------------------------- reads
    @classmethod
    def get(cls, items_id: int, **params: Any) -> dict[str, Any]:
        """Return one item.

        Args:
            items_id: Item id.
            **params: Extra API parameters (``expand_dropdowns``, ``with_logs``...).

        Returns:
            The item fields.

        Raises:
            NotFoundError: When the item does not exist.
        """
        return cls._connector().get_item(cls._itemtype(), items_id, **params)

    @classmethod
    def get_all(cls, **params: Any) -> list[dict[str, Any]]:
        """Return the items of the itemtype.

        Args:
            **params: Extra API parameters (``range``, ``sort``, ``order``, ``searchText``,
                ``is_deleted``, ``expand_dropdowns``...).

        Returns:
            The items (empty list when there is none).
        """
        return cls._connector().get_all_items(cls._itemtype(), **params)

    @classmethod
    def search(cls, criteria: Sequence[dict[str, Any]] | None = None, *,
               forcedisplay: Sequence[int | str] | None = None,
               metacriteria: Sequence[dict[str, Any]] | None = None, **params: Any) -> list[dict[str, Any]]:
        """Run the GLPI search engine on the itemtype.

        Args:
            criteria: ``[{"field": <id or uid>, "searchtype": "equals", "value": ...}]``.
            forcedisplay: Fields (id or uid) to include in each row.
            metacriteria: Criteria on linked itemtypes.
            **params: Extra API parameters (``range``, ``sort``, ``order``...).

        Returns:
            Rows indexed by field id (as string); empty list when nothing matches.
        """
        return cls._connector().search(cls._itemtype(), criteria, forcedisplay=forcedisplay,
                                       metacriteria=metacriteria, **params)

    @classmethod
    def get_sub_items(cls, items_id: int, sub_itemtype: str, **params: Any) -> list[dict[str, Any]]:
        """Return the sub-items of one item.

        Args:
            items_id: Parent id.
            sub_itemtype: Child itemtype (e.g. ``Log``, ``NetworkPort``).
            **params: Extra API parameters.

        Returns:
            The sub-items (empty list when there is none).
        """
        return cls._connector().get_sub_items(cls._itemtype(), items_id, sub_itemtype, **params)

    @classmethod
    def search_options(cls, raw: bool = False) -> dict[str, Any]:
        """Return the search options of the itemtype.

        Args:
            raw: Return the options as provided by the GLPI core.

        Returns:
            Search options indexed by field id.
        """
        return cls._connector().list_search_options(cls._itemtype(), raw)

    @classmethod
    def field_id(cls, uid: str, refresh: bool = False) -> int:
        """Translate a field uid into its search option id.

        Args:
            uid: Field uid without the itemtype prefix (e.g. ``Entity.completename``).
            refresh: Reload the search options from the server.

        Returns:
            The field id.

        Raises:
            BadRequestError: When the uid is unknown.
        """
        return cls._connector().field_id(cls._itemtype(), uid, refresh)

    @classmethod
    def field_uid(cls, field_id: int, refresh: bool = False) -> str:
        """Translate a search option id into its uid.

        Args:
            field_id: Field id.
            refresh: Reload the search options from the server.

        Returns:
            The field uid without the itemtype prefix.

        Raises:
            BadRequestError: When the id is unknown.
        """
        return cls._connector().field_uid(cls._itemtype(), field_id, refresh)

    # ------------------------------------------------------------------- writes
    @classmethod
    def add(cls, data: dict[str, Any]) -> int:
        """Create one item.

        Args:
            data: Field values (not modified).

        Returns:
            The id of the created item.

        Raises:
            BadRequestError: When GLPI refuses the item.
        """
        return _single_id(lambda: cls._connector().add_items(cls._itemtype(), [dict(data)]))

    @classmethod
    def add_many(cls, items: Sequence[dict[str, Any]]) -> list[int]:
        """Create several items in one request.

        Args:
            items: Field values of each item (not modified).

        Returns:
            The created ids, in input order (``[]`` without request for an empty list).

        Raises:
            PartialOperationError: When only some items were created.
        """
        if not items:
            return []
        results = cls._connector().add_items(cls._itemtype(), [dict(item) for item in items])
        return [int(result.id) for result in results if result.id is not None]

    @classmethod
    def update(cls, items_id: int, data: dict[str, Any]) -> None:
        """Update one item.

        Args:
            items_id: Item id.
            data: Field values to change (not modified).

        Raises:
            NotFoundError: When the item does not exist.
        """
        connector = cls._connector()
        _single(lambda: connector.update_items(cls._itemtype(), [{**data, "id": items_id}]), cls._itemtype(), items_id)

    @classmethod
    def update_many(cls, items: Sequence[dict[str, Any]]) -> None:
        """Update several items in one request.

        Args:
            items: Field values of each item, each one with its ``id`` (not modified).

        Raises:
            PartialOperationError: When only some items were updated.
        """
        if not items:
            return
        cls._connector().update_items(cls._itemtype(), [dict(item) for item in items])

    @classmethod
    def delete(cls, items_id: int, *, force_purge: bool = False, history: bool = True) -> None:
        """Delete (or purge) one item.

        Args:
            items_id: Item id.
            force_purge: Purge instead of moving to the trash bin.
            history: Keep the deletion in the history.

        Raises:
            NotFoundError: When the item does not exist.
        """
        connector = cls._connector()
        _single(lambda: connector.delete_items(cls._itemtype(), [items_id], force_purge=force_purge, history=history),
                cls._itemtype(), items_id)

    @classmethod
    def delete_many(cls, ids: Sequence[int], *, force_purge: bool = False, history: bool = True) -> None:
        """Delete (or purge) several items in one request.

        Args:
            ids: Item ids.
            force_purge: Purge instead of moving to the trash bin.
            history: Keep the deletion in the history.

        Raises:
            PartialOperationError: When only some items were deleted.
        """
        if not ids:
            return
        cls._connector().delete_items(cls._itemtype(), list(ids), force_purge=force_purge, history=history)

    # --------------------------------------------------------------- sub-items
    @classmethod
    def add_sub_item(cls, items_id: int, sub_itemtype: str, data: dict[str, Any]) -> int:
        """Create one sub-item under an item.

        Args:
            items_id: Parent id.
            sub_itemtype: Child itemtype.
            data: Field values (not modified).

        Returns:
            The id of the created sub-item.
        """
        connector = cls._connector()
        return _single_id(lambda: connector.add_sub_items(cls._itemtype(), items_id, sub_itemtype, [dict(data)]))

    @classmethod
    def update_sub_item(cls, items_id: int, sub_itemtype: str, sub_id: int, data: dict[str, Any]) -> None:
        """Update one sub-item under an item.

        Args:
            items_id: Parent id.
            sub_itemtype: Child itemtype.
            sub_id: Sub-item id.
            data: Field values to change (not modified).
        """
        connector = cls._connector()
        _single(lambda: connector.update_sub_items(cls._itemtype(), items_id, sub_itemtype, [{**data, "id": sub_id}]),
                sub_itemtype, sub_id)

    @classmethod
    def delete_sub_item(cls, items_id: int, sub_itemtype: str, sub_id: int) -> None:
        """Delete one sub-item under an item.

        Args:
            items_id: Parent id.
            sub_itemtype: Child itemtype.
            sub_id: Sub-item id.
        """
        connector = cls._connector()
        _single(lambda: connector.delete_sub_items(cls._itemtype(), items_id, sub_itemtype, [sub_id]),
                sub_itemtype, sub_id)

    # ------------------------------------------------------------------ helpers
    @classmethod
    def _for(cls, itemtype: str) -> type[CommonDBTM]:
        """Return a model class bound to another itemtype (internal helper).

        Args:
            itemtype: GLPI itemtype.

        Returns:
            A ``CommonDBTM`` subclass for ``itemtype``.
        """
        return _bound_class(itemtype)


@functools.cache
def _bound_class(itemtype: str) -> type[CommonDBTM]:
    """Create (once) a ``CommonDBTM`` subclass for an itemtype.

    Args:
        itemtype: GLPI itemtype.

    Returns:
        The subclass.
    """
    return type(itemtype, (CommonDBTM,), {"_glpi_name": itemtype})


def _failure(write: Callable[[], list[OperationResult]]) -> tuple[list[OperationResult], str, str | None]:
    """Run a one-item write and collect its per-item failure, if any.

    Args:
        write: The connector call.

    Returns:
        ``(results, failure_message, error_code)``; the message is empty on success.
    """
    try:
        results = write()
    except PartialOperationError as exc:
        # GLPI reports a one-item failure as per-item results
        failed = exc.failed or exc.results
        message = "; ".join(result.message for result in failed if result.message) or "item not processed"
        return exc.results, message, exc.error_code
    failed = [result for result in results if not result.ok]
    if failed:
        return results, failed[0].message or "item not processed", None
    return results, "", None


def _single(write: Callable[[], list[OperationResult]], itemtype: str, items_id: int) -> list[OperationResult]:
    """Run a one-item update or delete and turn a per-item failure into one error.

    GLPI only explains per-item failures with translated text, so the item is
    read back to tell a missing item from a refused operation.

    Args:
        write: The connector call.
        itemtype: Itemtype of the written item.
        items_id: Id of the written item.

    Returns:
        The results.

    Raises:
        NotFoundError: When the item does not exist.
        PermissionDeniedError: When the item cannot be read either.
        BadRequestError: When the item exists but GLPI refused the operation (rights, rules...).
    """
    results, message, error_code = _failure(write)
    if not message:
        return results
    # A missing (or unreadable) item raises NotFoundError (or PermissionDeniedError) here
    Glpi.connector().get_item(itemtype, items_id)
    raise BadRequestError(message, error_code=error_code)


def _single_id(write: Callable[[], list[OperationResult]]) -> int:
    """Run a one-item addition and return the created id.

    Args:
        write: The connector call.

    Returns:
        The created id.

    Raises:
        BadRequestError: When GLPI refused the item.
    """
    results, message, error_code = _failure(write)
    if message or not results or results[0].id is None:
        raise BadRequestError(message or "no id returned", error_code=error_code)
    return int(results[0].id)
