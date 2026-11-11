"""Public API rules: naming, annotations, class-level methods and import side effects."""

from __future__ import annotations

import importlib
import inspect
import re
import subprocess
import sys
from typing import Any

import pytest

SUBPACKAGES = ("assets", "assistance", "management", "tools", "administration", "dropdowns", "components")
SNAKE_CASE = re.compile(r"^[a-z][a-z0-9]*(_[a-z0-9]+)*$")


def _exported_classes() -> list[type]:
    """Collect the classes exported by the domain subpackages, plus the core models.

    Returns:
        The classes, without duplicates.
    """
    classes: list[type] = []
    for name in SUBPACKAGES:
        module = importlib.import_module(f"glpi_api_hero.{name}")
        classes += [getattr(module, item) for item in module.__all__]
    from glpi_api_hero import CommonDBTM, GenericItem

    return [CommonDBTM, GenericItem, *classes]


def _public_members(cls: type) -> list[tuple[str, Any]]:
    """List the public callables defined in a class body.

    Args:
        cls: Model class.

    Returns:
        ``(name, raw attribute)`` pairs.
    """
    return [(name, attr) for name, attr in vars(cls).items()
            if not name.startswith("_") and callable(getattr(attr, "__func__", attr))]


CLASSES = _exported_classes()


@pytest.mark.parametrize("cls", CLASSES, ids=lambda cls: cls.__name__)
def test_public_methods_are_snake_case(cls: type) -> None:
    """Every public method name is ``snake_case``.

    Args:
        cls: Exported model class.
    """
    assert [name for name, _ in _public_members(cls) if not SNAKE_CASE.match(name)] == []


@pytest.mark.parametrize("cls", CLASSES, ids=lambda cls: cls.__name__)
def test_public_methods_are_class_level(cls: type) -> None:
    """Models are never instantiated: public methods are class or static methods (R8).

    Args:
        cls: Exported model class.
    """
    offenders = [name for name, attr in _public_members(cls) if not isinstance(attr, (classmethod, staticmethod))]
    assert offenders == []


@pytest.mark.parametrize("cls", CLASSES, ids=lambda cls: cls.__name__)
def test_public_methods_are_annotated(cls: type) -> None:
    """Every public method annotates its parameters and its return value.

    Args:
        cls: Exported model class.
    """
    missing = []
    for name, attr in _public_members(cls):
        signature = inspect.signature(attr.__func__)
        if signature.return_annotation is inspect.Signature.empty:
            missing.append(f"{name} (return)")
        for index, (param_name, param) in enumerate(signature.parameters.items()):
            # The first parameter is ``cls``
            if index and param.annotation is inspect.Parameter.empty:
                missing.append(f"{name}({param_name})")
    assert missing == []


def test_top_level_import_does_not_load_domain_modules() -> None:
    """``import glpi_api_hero`` stays free of the domain subpackages (and of import cycles)."""
    code = (
        "import sys, glpi_api_hero;"
        "bad = [m for m in sys.modules if m.startswith('glpi_api_hero.') and m.split('.')[1] in "
        f"{set(SUBPACKAGES)!r}];"
        "sys.exit(1 if bad else 0)"
    )
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr


def test_top_level_exports() -> None:
    """The top-level package exports the session, the generic models, the exceptions and the version."""
    import glpi_api_hero

    assert {"Glpi", "GenericItem", "CommonDBTM", "GlpiError", "__version__"} <= set(glpi_api_hero.__all__)
    assert not {"Ticket", "User", "Location", "Computer", "ApiCommunication"} & set(glpi_api_hero.__all__)
