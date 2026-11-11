"""Clusters (GLPI ``Cluster``)."""

from __future__ import annotations

from typing import Any

from glpi_api_hero.core.capabilities import (
    HasAppliances,
    HasContracts,
    HasDocuments,
    HasLogs,
    HasNetworkPorts,
    HasTickets,
)


class Cluster(HasNetworkPorts, HasContracts, HasDocuments, HasAppliances, HasTickets, HasLogs):
    """GLPI ``Cluster`` (Management > Clusters)."""

    @classmethod
    def get_items(cls, cluster_id: int, **params: Any) -> list[dict[str, Any]]:
        """Return the members of the cluster (``Item_Cluster``).

        Args:
            cluster_id: Id of the parent.
            **params: Extra API parameters.

        Returns:
            The rows.
        """
        return cls.get_sub_items(cluster_id, "Item_Cluster", **params)
