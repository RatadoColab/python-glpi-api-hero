"""Every public method of the exported models has a complete Google-style docstring."""

from __future__ import annotations

import ast
import importlib
import inspect
import textwrap
from typing import Any

import pytest

SUBPACKAGES = ("administration", "assets", "assistance", "components", "dropdowns", "management", "tools")


def _classes() -> list[tuple[str, type]]:
    """Collect the exported classes of the top level, the core and the subpackages.

    Returns:
        ``(label, class)`` pairs.
    """
    found: dict[type, str] = {}
    modules = ["glpi_api_hero", "glpi_api_hero.core", *[f"glpi_api_hero.{name}" for name in SUBPACKAGES]]
    for module_name in modules:
        module = importlib.import_module(module_name)
        for name in getattr(module, "__all__", []):
            obj = getattr(module, name)
            if inspect.isclass(obj) and obj.__module__.startswith("glpi_api_hero"):
                found.setdefault(obj, f"{module_name}.{name}")
    return sorted((label, cls) for cls, label in found.items())


def _methods(cls: type) -> list[tuple[str, Any]]:
    """List the public methods defined by a class or inherited from the library.

    Args:
        cls: Class to inspect.

    Returns:
        ``(name, function)`` pairs.
    """
    result = []
    for name in dir(cls):
        if name.startswith("_"):
            continue
        static = inspect.getattr_static(cls, name)
        if isinstance(static, (classmethod, staticmethod)):
            function = static.__func__
            if (getattr(function, "__module__", None) or "").startswith("glpi_api_hero"):
                result.append((name, function))
    return result


CASES = [(f"{label}.{name}", function) for label, cls in _classes() for name, function in _methods(cls)]


@pytest.mark.parametrize("function", [f for _, f in CASES], ids=[i for i, _ in CASES])
def test_public_method_docstring(function: Any) -> None:
    """Summary line ending in a period, plus Args/Returns/Raises when the signature or body needs them."""
    doc = inspect.getdoc(function)
    assert doc, "missing docstring"
    summary = doc.strip().splitlines()[0]
    assert summary.endswith("."), f"summary must end with a period: {summary!r}"
    signature = inspect.signature(function)
    params = [name for name in signature.parameters if name not in ("cls", "self")]
    if params:
        assert "Args:" in doc, "missing Args section"
    if signature.return_annotation not in (None, "None", inspect.Signature.empty):
        assert "Returns:" in doc or "Yields:" in doc, "missing Returns section"
    source = textwrap.dedent(inspect.getsource(function))
    raises = any(isinstance(node, ast.Raise) for node in ast.walk(ast.parse(source)))
    if raises:
        assert "Raises:" in doc, "missing Raises section"
