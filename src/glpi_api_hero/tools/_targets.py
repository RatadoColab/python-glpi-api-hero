"""Aggregation of the visibility targets of Reminder and KnowbaseItem."""

from __future__ import annotations

from typing import Any

from glpi_api_hero.core.common_dbtm import CommonDBTM


def collect_targets(model: type[CommonDBTM], items_id: int, relations: dict[str, tuple[str, str]],
                    **params: Any) -> list[dict[str, Any]]:
    """Read every target relation of an item and tag the rows.

    Args:
        model: Parent model.
        items_id: Parent id.
        relations: ``kind`` -> ``(relation itemtype, column with the target id)``.
        **params: Extra API parameters (applied to each request).

    Returns:
        The relation rows (copies) with ``kind`` and ``target_id``; ``[]`` when there is no target.
    """
    rows: list[dict[str, Any]] = []
    for kind, (itemtype, column) in relations.items():
        rows.extend({**row, "kind": kind, "target_id": row.get(column)}
                    for row in model.get_sub_items(items_id, itemtype, **params))
    return rows
