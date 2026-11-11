"""Factory of models for itemtypes without a dedicated class."""

from __future__ import annotations

from glpi_api_hero.core.common_dbtm import CommonDBTM


class GenericItem(CommonDBTM):
    """Placeholder of the generic model factory (implemented in phase 04.2)."""

    @classmethod
    def of(cls, itemtype: str) -> type[CommonDBTM]:
        """Return a model class bound to ``itemtype``.

        Args:
            itemtype: GLPI itemtype (e.g. ``PluginFooBar``).

        Returns:
            A ``CommonDBTM`` subclass for ``itemtype``.

        Raises:
            NotImplementedError: Until phase 04.2 implements the factory.
        """
        raise NotImplementedError("GenericItem.of() is implemented in phase 04.2")
