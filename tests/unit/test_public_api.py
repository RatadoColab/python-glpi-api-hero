"""Public API rules: naming, annotations, class-level methods and import side effects."""

from __future__ import annotations

import importlib
import inspect
import json
import re
import subprocess
import sys
from pathlib import Path
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


MIGRATION_GUIDE = Path(__file__).resolve().parents[2] / "docs" / "migration.md"
FIXTURE = Path(__file__).resolve().parents[1] / "characterization" / "fixtures" / "requests.json"
GUIDE_SECTION = "## Renamed, moved and removed API"
OLD_NAME = re.compile(r"[A-Za-z_]+\.[A-Za-z_]+")
NEW_TARGET = re.compile(r"^([A-Za-z_][\w.]*):([A-Za-z_]\w*)(?:\.([A-Za-z_]\w*))?(?:\s*\(.*\))?$")


def _guide_rows() -> list[tuple[str, str]]:
    """Read the ``| old | new |`` rows of the renamed/moved/removed table of the migration guide.

    Returns:
        ``(old cell, new cell)`` pairs, backticks stripped from the new cell target.
    """
    text = MIGRATION_GUIDE.read_text(encoding="utf-8")
    section = text.split(GUIDE_SECTION, 1)[1].split("\n## ", 1)[0]
    rows = []
    for line in section.splitlines():
        if not line.startswith("|") or line.startswith("|---") or line.startswith("| old "):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split(" | ", 1)]
        rows.append((cells[0], cells[1]))
    return rows


def _new_target(cell: str) -> str:
    """Extract the target of a ``new`` cell: its first backticked span, or the whole cell.

    Args:
        cell: Raw ``new`` cell.

    Returns:
        The target text.
    """
    match = re.match(r"^`([^`]+)`", cell)
    return match.group(1) if match else cell


def _resolve_class(name: str) -> type | None:
    """Find a model or helper class by name in the top-level package and the domain subpackages.

    Args:
        name: Class name.

    Returns:
        The class, or ``None`` when no module exports it.
    """
    for module_name in ("glpi_api_hero", *(f"glpi_api_hero.{sub}" for sub in SUBPACKAGES)):
        module = importlib.import_module(module_name)
        if hasattr(module, name):
            return getattr(module, name)
    return None


def test_migration_guide_targets_exist() -> None:
    """Every ``new`` entry names an existing class/method, or states why the old name was removed."""
    errors = []
    rows = _guide_rows()
    assert rows, "no rows found in the migration guide"
    for old, new in rows:
        target = _new_target(new)
        removed = re.match(r"^removed \((.+)\)", target)
        if removed:
            continue
        match = NEW_TARGET.match(target)
        if not match:
            errors.append(f"{old}: unrecognized format {target!r}")
            continue
        module_name, class_name, method = match.groups()
        try:
            owner = getattr(importlib.import_module(module_name), class_name)
        except (ImportError, AttributeError):
            errors.append(f"{old}: {module_name}:{class_name} not found")
            continue
        if method and not hasattr(owner, method):
            errors.append(f"{old}: {class_name}.{method} not found")
    assert errors == []


def test_migration_guide_covers_old_public_methods() -> None:
    """Every old public method of the characterization fixture is listed in the guide or still exists."""
    listed = {name for old, _ in _guide_rows() for name in OLD_NAME.findall(old)}
    listed_methods = {name.split(".", 1)[1] for name in listed}
    # A bare class name in the old column covers every method of that class
    listed_classes = {name for old, _ in _guide_rows() for name in re.findall(r"(?<![\w.])[A-Z]\w*(?![\w.])", old)}
    old_calls = {entry["call"] for entry in json.loads(FIXTURE.read_text(encoding="utf-8"))}
    missing = []
    for call in sorted(old_calls):
        class_name, method = call.split(".", 1)
        # Methods inherited from CommonDBTM are listed once, under the base class
        if call in listed or class_name in listed_classes or method in listed_methods or method.startswith("_"):
            continue
        owner = _resolve_class(class_name)
        if owner is not None and hasattr(owner, method):
            continue
        missing.append(call)
    assert missing == []
