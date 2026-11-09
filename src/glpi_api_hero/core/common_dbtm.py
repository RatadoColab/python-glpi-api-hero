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
from collections.abc import Sequence
from typing import Any, ClassVar

from glpi_api_hero.core.connector import Connector
from glpi_api_hero.core.session import Glpi
from glpi_api_hero.core.types import OperationResult
from glpi_api_hero.exceptions import (
    BadRequestError,
    GlpiAPIError,
    NotFoundError,
    PartialOperationError,
    PermissionDeniedError,
)


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
        results = cls._connector().add_items(cls._itemtype(), [dict(data)])
        return _single_id(results)

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
        _single(cls._connector().update_items, cls._itemtype(), [{"id": items_id, **data}])

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
        delete = functools.partial(cls._connector().delete_items, force_purge=force_purge, history=history)
        _single(delete, cls._itemtype(), [items_id])

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


def _single(operation: Any, target: str, payload: list[Any]) -> list[OperationResult]:
    """Run a one-item write and turn a per-item failure into a single-item error.

    Args:
        operation: Connector write method (possibly partially applied).
        target: Itemtype (first argument of ``operation``).
        payload: One-element payload.

    Returns:
        The results.

    Raises:
        PermissionDeniedError: When GLPI reports a missing right for the item.
        NotFoundError: When GLPI reports any other per-item failure (usually a missing item).
    """
    try:
        results = operation(target, payload)
    except PartialOperationError as exc:
        # A one-item bulk failure is reported by GLPI as per-item results
        message = "; ".join(result.message for result in exc.failed if result.message) or str(exc)
        raise _item_error(message, exc.error_code) from exc
    failed = [result for result in results if not result.ok]
    if failed:
        raise _item_error(failed[0].message or f"{target} item not processed", None)
    return results


def _item_error(message: str, error_code: str | None) -> GlpiAPIError:
    """Choose the error of a failed single-item write from the GLPI message.

    GLPI only reports per-item failures as text: "You don't have permission..."
    for rights and "Item not found" otherwise (messages may be translated).

    Args:
        message: Per-item message.
        error_code: GLPI error key of the response.

    Returns:
        ``PermissionDeniedError`` for rights messages, ``NotFoundError`` otherwise.
    """
    if "permission" in message.lower():
        return PermissionDeniedError(message, error_code=error_code)
    return NotFoundError(message, error_code=error_code)


def _single_id(results: list[OperationResult]) -> int:
    """Return the created id of a one-item addition.

    Args:
        results: Per-item results.

    Returns:
        The created id.

    Raises:
        BadRequestError: When no id was returned.
    """
    if not results or results[0].id is None:
        message = results[0].message if results else "no id returned"
        raise BadRequestError(message or "no id returned")
    return int(results[0].id)
