"""Run the characterization scenarios and (re)write the fixture.

Usage:
    python -m tests.characterization.record

The same runner is used by ``test_http_contract.py`` to compare the current
behavior with the recorded fixture.
"""

from __future__ import annotations

import contextlib
import copy
import datetime as _dt
import importlib
import io
import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any
from unittest import mock

from tests.characterization.scenarios import MAPPERS, SCENARIOS
from tests.conftest import (
    APP_TOKEN,
    BASE_URL,
    PASSWORD,
    USER_TOKEN,
    USERNAME,
    GlpiMock,
    mocked_glpi,
    reset_api_state,
)

FIXTURE = Path(__file__).parent / "fixtures" / "requests.json"

# Fixed clock used by time-dependent code (dashboard SLA criteria)
FROZEN_NOW = _dt.datetime(2026, 1, 15, 10, 30, 0)


class _FrozenDatetime(_dt.datetime):
    """``datetime`` replacement with a fixed ``now``."""

    @classmethod
    def now(cls, tz: _dt.tzinfo | None = None) -> _FrozenDatetime:
        """Return the frozen instant (``tz`` is ignored)."""
        return cls(*FROZEN_NOW.timetuple()[:6])


class _FrozenDate(_dt.date):
    """``date`` replacement with a fixed ``today``."""

    @classmethod
    def today(cls) -> _FrozenDate:
        """Return the frozen day."""
        return cls(FROZEN_NOW.year, FROZEN_NOW.month, FROZEN_NOW.day)


def _package() -> Any:
    """Import the library package.

    Returns:
        The ``glpi_api_hero`` module.
    """
    return importlib.import_module("glpi_api_hero")


def resolve_class(name: str) -> Any:
    """Resolve a class name exported by the library.

    Args:
        name: Class name (e.g. ``Location``).

    Returns:
        The class object.
    """
    return getattr(_package(), name)


def resolve(value: Any) -> Any:
    """Resolve ``@mapper:`` and ``@glpi:`` placeholders recursively.

    Args:
        value: Argument value from a scenario.

    Returns:
        The value with placeholders replaced by live objects.
    """
    if isinstance(value, str) and value.startswith("@mapper:"):
        return MAPPERS[value.split(":", 1)[1]]
    if isinstance(value, str) and value.startswith("@glpi:"):
        # Bound method of the live connection object
        return getattr(resolve_class("ApiCommunication").glpi, value.split(":", 1)[1])
    if isinstance(value, list):
        return [resolve(v) for v in value]
    if isinstance(value, dict):
        return {k: resolve(v) for k, v in value.items()}
    return value


def to_jsonable(value: Any) -> Any:
    """Convert a result into a JSON-serializable value.

    Args:
        value: Any value returned by the library.

    Returns:
        The same data with tuples as lists and unknown objects as a type marker.
    """
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, (list, tuple)):
        return [to_jsonable(v) for v in value]
    if isinstance(value, dict):
        return {str(k): to_jsonable(v) for k, v in value.items()}
    # Objects (connection, sessions...) are recorded by type only
    return {"__type__": type(value).__name__}


def _steps(scenario: dict[str, Any]) -> list[dict[str, Any]]:
    """Return the steps of a scenario (a single step when ``steps`` is absent).

    Args:
        scenario: Scenario dict.

    Returns:
        List of ``{"call", "args", "kwargs"}``.
    """
    if "steps" in scenario:
        return scenario["steps"]
    return [{"call": scenario["call"], "args": scenario.get("args", []),
             "kwargs": scenario.get("kwargs", {})}]


def _open_session(kind: str | None) -> None:
    """Open the session requested by a scenario before the capture starts.

    Args:
        kind: ``"user_token"``, ``"basic"`` or ``None``.
    """
    api = resolve_class("ApiCommunication")
    if kind == "user_token":
        api.setConnectionParameters(BASE_URL, APP_TOKEN, usertoken=USER_TOKEN)
        api.initSession()
    elif kind == "basic":
        api.setConnectionParameters(BASE_URL, APP_TOKEN, user=USERNAME, passwd=PASSWORD)
        api.initSession()


@contextlib.contextmanager
def _frozen_clock() -> Iterator[None]:
    """Freeze ``date``/``datetime`` in the modules that read the clock."""
    with contextlib.ExitStack() as stack:
        for module_name in ("glpi_api_hero.ticket_dashboard",):
            # Modules may move during the refactoring; patch only what exists
            try:
                module = importlib.import_module(module_name)
            except ImportError:
                continue
            if hasattr(module, "datetime"):
                stack.enter_context(mock.patch.object(module, "datetime", _FrozenDatetime))
            if hasattr(module, "date"):
                stack.enter_context(mock.patch.object(module, "date", _FrozenDate))
        yield


def _inspect(kind: str | None) -> Any:
    """Collect extra state requested by a scenario.

    Args:
        kind: ``"session_verify"`` or ``None``.

    Returns:
        The inspected value, or ``None``.
    """
    api = resolve_class("ApiCommunication")
    if kind == "session_verify":
        return api.glpi.session.verify if api.glpi is not None else None
    return None


def run_scenario(scenario: dict[str, Any], glpi: GlpiMock) -> dict[str, Any]:
    """Execute one scenario against the simulator.

    Args:
        scenario: Scenario dict from ``SCENARIOS``.
        glpi: Active simulator.

    Returns:
        The fixture entry: requests plus ``returns`` or ``raises`` (and optional extras).
    """
    reset_api_state()
    glpi.overrides.clear()
    _open_session(scenario.get("session", "user_token"))
    # Overrides only apply to the captured part of the scenario
    for override in scenario.get("responses", []):
        glpi.override(override["method"], override["path"], override.get("status", 200),
                      override.get("body"), override.get("headers"), override.get("error"))
    glpi.reset_calls()

    entry: dict[str, Any] = {"id": scenario["id"], "call": scenario["call"],
                             "args": scenario.get("args", []), "kwargs": scenario.get("kwargs", {})}
    if "steps" in scenario:
        entry["steps"] = scenario["steps"]
    stdout = io.StringIO()
    result: Any = None
    error: BaseException | None = None
    args_after: list[Any] = []
    original_args: list[Any] = []
    with _frozen_clock(), contextlib.redirect_stdout(stdout):
        for step in _steps(scenario):
            cls_name, method = step["call"].split(".", 1)
            args = resolve(copy.deepcopy(step.get("args", [])))
            original_args = resolve(copy.deepcopy(step.get("args", [])))
            kwargs = resolve(copy.deepcopy(step.get("kwargs", {})))
            try:
                result = getattr(resolve_class(cls_name), method)(*args, **kwargs)
            except Exception as exc:  # noqa: BLE001 - the oracle records any exception
                error = exc
                break
            finally:
                args_after = args

    entry["requests"] = glpi.captured()
    if error is not None:
        message = None if scenario.get("message") == "type_only" else str(error)
        entry["raises"] = {"type": type(error).__name__, "message": message}
    else:
        entry["returns"] = to_jsonable(result)
    # Mutation of the caller's arguments (of the last executed step) is observable behavior
    if to_jsonable(args_after) != to_jsonable(original_args):
        entry["args_after"] = to_jsonable(args_after)
    if stdout.getvalue():
        entry["stdout"] = stdout.getvalue()
    if scenario.get("state"):
        api = resolve_class("ApiCommunication")
        entry["state"] = {"connection": to_jsonable(api.glpi_connection),
                          "environment": to_jsonable(api.glpi_environment),
                          "connected": api.glpi is not None}
    if scenario.get("inspect"):
        entry["inspect"] = to_jsonable(_inspect(scenario["inspect"]))
    if scenario.get("known_bug"):
        entry["known_bug"] = scenario["known_bug"]
    reset_api_state()
    return entry


def record_all() -> list[dict[str, Any]]:
    """Run every scenario and return the fixture entries.

    Returns:
        One entry per scenario, in table order.
    """
    entries = []
    for glpi in mocked_glpi():
        for scenario in SCENARIOS:
            entries.append(run_scenario(scenario, glpi))
    return entries


def main() -> None:
    """Rewrite ``fixtures/requests.json`` from the current behavior."""
    FIXTURE.parent.mkdir(parents=True, exist_ok=True)
    entries = record_all()
    # One scenario per line keeps the fixture diff readable scenario by scenario
    lines = [json.dumps(entry, ensure_ascii=False, sort_keys=True) for entry in entries]
    FIXTURE.write_text("[\n" + ",\n".join(lines) + "\n]\n", encoding="utf-8")
    print(f"{len(entries)} scenarios written to {FIXTURE}")


if __name__ == "__main__":
    main()
