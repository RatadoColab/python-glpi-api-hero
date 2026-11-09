"""API-version agnostic contract between the models and a GLPI API.

Models only talk to a :class:`Connector`. Each implementation translates the
normalized calls below into its own API (legacy ``apirest.php`` today, the
high-level API of GLPI 11/12 later) and returns normalized types:

* single item → ``dict``; collections → ``list[dict]``;
* writes → ``list[OperationResult]`` (one per input item);
* errors → exceptions of :mod:`glpi_api_hero.exceptions`.
"""

from __future__ import annotations

import abc
import re
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from glpi_api_hero.core.types import OperationResult
from glpi_api_hero.exceptions import BadRequestError, UnsupportedOperationError


class Connector(abc.ABC):
    """Abstract connector: one open session against one GLPI server."""

    def __init__(self) -> None:
        """Initialize the search option cache shared by the field helpers."""
        # itemtype -> {uid (without itemtype prefix): field id}
        self._field_cache: dict[str, dict[str, int]] = {}

    # ------------------------------------------------------------------ session
    @abc.abstractmethod
    def init_session(self) -> None:
        """Open the session on the server.

        Raises:
            AuthenticationError: When the credentials are refused.
            GlpiConnectionError: When the server cannot be reached.
        """

    @abc.abstractmethod
    def kill_session(self) -> None:
        """Close the session on the server."""

    @abc.abstractmethod
    def get_my_profiles(self) -> list[dict[str, Any]]:
        """Return the profiles of the logged user."""

    @abc.abstractmethod
    def get_active_profile(self) -> dict[str, Any]:
        """Return the active profile."""

    @abc.abstractmethod
    def set_active_profile(self, profiles_id: int) -> None:
        """Change the active profile.

        Args:
            profiles_id: Profile id.
        """

    @abc.abstractmethod
    def get_my_entities(self, is_recursive: bool = False) -> list[dict[str, Any]]:
        """Return the entities reachable by the logged user.

        Args:
            is_recursive: Include sub-entities.
        """

    @abc.abstractmethod
    def get_active_entities(self) -> dict[str, Any]:
        """Return the active entities."""

    @abc.abstractmethod
    def set_active_entities(self, entities_id: int, is_recursive: bool = False) -> None:
        """Change the active entity.

        Args:
            entities_id: Entity id.
            is_recursive: Also activate the sub-entities.
        """

    @abc.abstractmethod
    def get_full_session(self) -> dict[str, Any]:
        """Return the server-side session data."""

    @abc.abstractmethod
    def get_config(self) -> dict[str, Any]:
        """Return the GLPI configuration visible to the session."""

    # -------------------------------------------------------------------- reads
    @abc.abstractmethod
    def get_item(self, itemtype: str, items_id: int, **params: Any) -> dict[str, Any]:
        """Return one item.

        Args:
            itemtype: GLPI itemtype.
            items_id: Item id.
            **params: Extra API parameters.

        Raises:
            NotFoundError: When the item does not exist.
        """

    @abc.abstractmethod
    def get_all_items(self, itemtype: str, **params: Any) -> list[dict[str, Any]]:
        """Return the items of an itemtype.

        Args:
            itemtype: GLPI itemtype.
            **params: Extra API parameters (range, sort, order, searchText...).
        """

    @abc.abstractmethod
    def get_sub_items(self, itemtype: str, items_id: int, sub_itemtype: str, **params: Any) -> list[dict[str, Any]]:
        """Return the sub-items of one item.

        Args:
            itemtype: Parent itemtype.
            items_id: Parent id.
            sub_itemtype: Child itemtype.
            **params: Extra API parameters.
        """

    @abc.abstractmethod
    def get_multiple_items(self, refs: Sequence[tuple[str, int]], **params: Any) -> list[dict[str, Any]]:
        """Return several items of possibly different itemtypes.

        Args:
            refs: ``(itemtype, id)`` pairs.
            **params: Extra API parameters.
        """

    @abc.abstractmethod
    def list_search_options(self, itemtype: str, raw: bool = False) -> dict[str, Any]:
        """Return the search options of an itemtype.

        Args:
            itemtype: GLPI itemtype.
            raw: Return the options as provided by the GLPI core.
        """

    @abc.abstractmethod
    def search(self, itemtype: str, criteria: Sequence[dict[str, Any]] | None = None, *,
               forcedisplay: Sequence[int | str] | None = None,
               metacriteria: Sequence[dict[str, Any]] | None = None, **params: Any) -> list[dict[str, Any]]:
        """Run the search engine.

        Args:
            itemtype: GLPI itemtype.
            criteria: Search criteria; ``field`` accepts a field id or uid.
            forcedisplay: Fields (id or uid) to include in each row.
            metacriteria: Criteria on linked itemtypes.
            **params: Extra API parameters (range, sort, order...).

        Returns:
            Rows indexed by field id (as string).
        """

    # ------------------------------------------------------------------- writes
    @abc.abstractmethod
    def add_items(self, itemtype: str, items: Sequence[dict[str, Any]]) -> list[OperationResult]:
        """Create items.

        Args:
            itemtype: GLPI itemtype.
            items: Field values of each item.

        Raises:
            PartialOperationError: When only some items were created.
        """

    @abc.abstractmethod
    def update_items(self, itemtype: str, items: Sequence[dict[str, Any]]) -> list[OperationResult]:
        """Update items (each one carries its ``id``).

        Args:
            itemtype: GLPI itemtype.
            items: Field values of each item, with ``id``.

        Raises:
            PartialOperationError: When only some items were updated.
        """

    @abc.abstractmethod
    def delete_items(self, itemtype: str, ids: Sequence[int], *, force_purge: bool = False,
                     history: bool = True) -> list[OperationResult]:
        """Delete (or purge) items.

        Args:
            itemtype: GLPI itemtype.
            ids: Ids of the items.
            force_purge: Purge instead of moving to the trash bin.
            history: Keep the deletion in the history.

        Raises:
            PartialOperationError: When only some items were deleted.
        """

    @abc.abstractmethod
    def add_sub_items(self, itemtype: str, items_id: int, sub_itemtype: str,
                      items: Sequence[dict[str, Any]]) -> list[OperationResult]:
        """Create sub-items under one item.

        Args:
            itemtype: Parent itemtype.
            items_id: Parent id.
            sub_itemtype: Child itemtype.
            items: Field values of each child.
        """

    @abc.abstractmethod
    def update_sub_items(self, itemtype: str, items_id: int, sub_itemtype: str,
                         items: Sequence[dict[str, Any]]) -> list[OperationResult]:
        """Update sub-items under one item (each one carries its ``id``).

        Args:
            itemtype: Parent itemtype.
            items_id: Parent id.
            sub_itemtype: Child itemtype.
            items: Field values of each child, with ``id``.
        """

    @abc.abstractmethod
    def delete_sub_items(self, itemtype: str, items_id: int, sub_itemtype: str,
                         ids: Sequence[int]) -> list[OperationResult]:
        """Delete sub-items under one item.

        Args:
            itemtype: Parent itemtype.
            items_id: Parent id.
            sub_itemtype: Child itemtype.
            ids: Ids of the children.
        """

    # ---------------------------------------------------------------- documents
    def upload_document(self, name: str, filepath: str | Path) -> int:
        """Upload a file as a new Document.

        Args:
            name: Document name.
            filepath: Path of the file to upload.

        Returns:
            The id of the created Document.

        Raises:
            UnsupportedOperationError: When the connector has no upload support.
        """
        raise UnsupportedOperationError(f"{type(self).__name__} does not support document upload")

    def download_document(self, documents_id: int, dirpath: str | Path, filename: str | None = None) -> Path:
        """Download the file of a Document.

        Args:
            documents_id: Document id.
            dirpath: Existing directory where the file is written.
            filename: File name; defaults to the name stored in GLPI.

        Returns:
            Path of the written file.

        Raises:
            UnsupportedOperationError: When the connector has no download support.
        """
        raise UnsupportedOperationError(f"{type(self).__name__} does not support document download")

    # ------------------------------------------------------------ field helpers
    def _field_map(self, itemtype: str, refresh: bool = False) -> dict[str, int]:
        """Return the cached ``uid → id`` map of an itemtype.

        Args:
            itemtype: GLPI itemtype.
            refresh: Reload the search options from the server.

        Returns:
            Field ids indexed by uid (without the ``<itemtype>.`` prefix).
        """
        if refresh or itemtype not in self._field_cache:
            prefix = re.compile(rf"^{re.escape(itemtype)}\.")
            options = self.list_search_options(itemtype)
            self._field_cache[itemtype] = {
                prefix.sub("", option["uid"]): int(field_id)
                for field_id, option in options.items()
                if isinstance(option, dict) and "uid" in option and str(field_id).isdigit()
            }
        return self._field_cache[itemtype]

    def field_id(self, itemtype: str, field: int | str, refresh: bool = False) -> int:
        """Translate a field uid into its search option id.

        Args:
            itemtype: GLPI itemtype.
            field: Field id (returned unchanged) or uid (e.g. ``Entity.completename``).
            refresh: Reload the search options from the server.

        Returns:
            The field id.

        Raises:
            BadRequestError: When the uid is unknown.
        """
        # Numeric values are already ids
        if isinstance(field, int) or str(field).isdigit():
            return int(field)
        mapping = self._field_map(itemtype, refresh)
        if str(field) not in mapping:
            raise BadRequestError(f"unknown search field {field!r} for {itemtype}", error_code="ERROR_FIELD_NOT_FOUND")
        return mapping[str(field)]

    def field_uid(self, itemtype: str, field_id: int | str, refresh: bool = False) -> str:
        """Translate a search option id into its uid.

        Args:
            itemtype: GLPI itemtype.
            field_id: Field id.
            refresh: Reload the search options from the server.

        Returns:
            The field uid (without the ``<itemtype>.`` prefix).

        Raises:
            BadRequestError: When the id is unknown.
        """
        reverse = {value: key for key, value in self._field_map(itemtype, refresh).items()}
        if not str(field_id).isdigit() or int(field_id) not in reverse:
            raise BadRequestError(f"unknown search field id {field_id!r} for {itemtype}",
                                  error_code="ERROR_FIELD_NOT_FOUND")
        return reverse[int(field_id)]
