"""Factory of models for itemtypes without a dedicated class (including plugin itemtypes)."""

from __future__ import annotations

import functools
import re
from typing import Any, NoReturn

from glpi_api_hero.core.common_dbtm import CommonDBTM

# Itemtype: identifier, optionally namespaced with single backslashes (``Glpi\Socket``)
_ITEMTYPE = re.compile(r"^[A-Za-z][A-Za-z0-9_]*(\\[A-Za-z][A-Za-z0-9_]*)*$")


def _not_instantiable(cls: type, *args: Any, **kwargs: Any) -> NoReturn:
    """Refuse the creation of instances: models are used through class methods only.

    Args:
        cls: The class being instantiated.
        *args: Ignored.
        **kwargs: Ignored.

    Raises:
        TypeError: Always.
    """
    raise TypeError(f"{cls.__name__} is not instantiable; use its class methods")


class _GenericMeta(type):
    """Metaclass giving the generated classes a readable ``repr``."""

    def __repr__(cls) -> str:
        """Describe the class by the itemtype it is bound to.

        Returns:
            ``<GenericItem 'Itemtype'>`` for generated classes.
        """
        itemtype = cls.__dict__.get("_glpi_name")
        return f"<GenericItem {itemtype!r}>" if itemtype else super().__repr__()


class GenericItem(CommonDBTM, metaclass=_GenericMeta):
    """Factory of ``CommonDBTM`` models for any GLPI itemtype.

    Example:
        >>> Line = GenericItem.of("Line")
        >>> Line.get(3)  # doctest: +SKIP
    """

    __new__ = _not_instantiable  # type: ignore[assignment]

    @classmethod
    @functools.cache
    def _build(cls, itemtype: str) -> type[CommonDBTM]:
        """Create (once per itemtype) the model class.

        Args:
            itemtype: Validated GLPI itemtype.

        Returns:
            The generated class.
        """
        name = "Generic" + itemtype.replace("\\", "")
        generated = _GenericMeta(name, (CommonDBTM,), {"_glpi_name": itemtype, "__new__": _not_instantiable,
                                                      "__module__": __name__, "__doc__": f"Model of ``{itemtype}``."})
        generated.__qualname__ = name
        return generated

    @classmethod
    def of(cls, itemtype: str) -> type[CommonDBTM]:
        """Return a model class bound to ``itemtype``.

        The result is always a dynamic ``CommonDBTM`` subclass, even when a typed model
        exists for the itemtype (``of("Computer")`` is not ``assets.Computer``). Calls with
        the same itemtype return the same class object.

        Args:
            itemtype: GLPI itemtype (e.g. ``Line``, ``PluginFooBar``, ``Glpi\\Socket``).

        Returns:
            A ``CommonDBTM`` subclass for ``itemtype``.

        Raises:
            ValueError: When ``itemtype`` is not a valid itemtype name (checked before any request).
        """
        if not isinstance(itemtype, str) or not _ITEMTYPE.fullmatch(itemtype):
            raise ValueError(f"invalid GLPI itemtype: {itemtype!r}")
        return cls._build(itemtype)
