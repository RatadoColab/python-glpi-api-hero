"""Documents (GLPI ``Document``)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from glpi_api_hero.core.capabilities import HasLogs, HasNotes


class Document(HasNotes, HasLogs):
    """GLPI ``Document`` (Management > Documents)."""

    @classmethod
    def get_items(cls, documents_id: int, **params: Any) -> list[dict[str, Any]]:
        """Return the items the document is attached to (``Document_Item``).

        Args:
            documents_id: Document id.
            **params: Extra API parameters.

        Returns:
            The link rows.
        """
        return cls.get_sub_items(documents_id, "Document_Item", **params)

    @classmethod
    def link_item(cls, documents_id: int, itemtype: str, items_id: int) -> int:
        """Attach the document to an item (``Document_Item``).

        Args:
            documents_id: Document id.
            itemtype: Itemtype of the item.
            items_id: Id of the item.

        Returns:
            The id of the link row.
        """
        return cls._for("Document_Item").add({"documents_id": documents_id, "itemtype": itemtype,
                                              "items_id": items_id})

    @classmethod
    def upload(cls, name: str, filepath: str | Path) -> int:
        """Upload a file as a new document (multipart, streamed from disk).

        Args:
            name: Document name.
            filepath: Path of the file.

        Returns:
            The id of the new document.

        Raises:
            FileNotFoundError: When the file does not exist (checked before any request).
        """
        path = Path(filepath)
        if not path.is_file():
            raise FileNotFoundError(f"file not found: {path}")
        return cls._connector().upload_document(name, path)

    @classmethod
    def download(cls, documents_id: int, dirpath: str | Path, filename: str | None = None, *,
                 overwrite: bool = False) -> Path:
        """Download the file of a document.

        The name comes from ``filename`` or from the ``Content-Disposition`` header, reduced to a plain file name
        (``document-<id>`` when nothing usable is left). The file is created owner-only.

        Args:
            documents_id: Document id.
            dirpath: Existing directory that receives the file.
            filename: Name to use instead of the stored one.
            overwrite: Replace a file that already exists.

        Returns:
            Path of the written file.

        Raises:
            ValueError: When the final path would not sit directly inside ``dirpath``.
            FileExistsError: When the file exists and ``overwrite`` is false.
        """
        return cls._connector().download_document(documents_id, dirpath, filename, overwrite=overwrite)
