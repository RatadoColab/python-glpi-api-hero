"""Run the characterization scenarios and (re)write the fixture.

Usage:
    python -m tests.characterization.record --normalized

The point A fields of each entry (``call``, ``args``, ``requests``, ``returns`` or
``raises``...) were recorded with the former ``glpi-api`` transport (commit 58be2a7)
and are never rewritten. ``--normalized`` runs the scenarios against the current
code (with the overrides of ``scenarios.V2``) and stores the result under ``v2``.
The requests must stay identical to point A unless the override declares
``requests_change`` (the decision that changed them).

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
import sys
from collections.abc import Iterator
from pathlib import Path
from typing import Any
from unittest import mock

from tests.characterization.scenarios import MAPPERS, SCENARIOS, normalized
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
    """Resolve ``@mapper:`` and ``@connector:`` placeholders recursively.

    Args:
        value: Argument value from a scenario.

    Returns:
        The value with placeholders replaced by live objects.
    """
    if isinstance(value, str) and value.startswith("@mapper:"):
        return MAPPERS[value.split(":", 1)[1]]
    if isinstance(value, str) and value.startswith("@connector:"):
        # Bound method of the live connector
        return getattr(resolve_class("Glpi").connector(), value.split(":", 1)[1])
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
    glpi = resolve_class("Glpi")
    if kind == "session_verify":
        return glpi.connector().verify if glpi.is_connected() else None
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
                          "connected": resolve_class("Glpi").is_connected()}
    if scenario.get("inspect"):
        entry["inspect"] = to_jsonable(_inspect(scenario["inspect"]))
    if scenario.get("known_bug"):
        entry["known_bug"] = scenario["known_bug"]
    reset_api_state()
    return entry


def run_normalized(scenario: dict[str, Any], glpi: GlpiMock) -> dict[str, Any]:
    """Execute the normalized (current) version of a scenario.

    Args:
        scenario: Scenario dict from ``SCENARIOS``.
        glpi: Active simulator.

    Returns:
        The ``v2`` fixture entry (without ``id``).
    """
    current = normalized(scenario)
    entry = run_scenario(current, glpi)
    entry.pop("id")
    # Decisions that justify a difference from point A are kept next to the result
    for key in ("requests_change", "fixed"):
        if key in current:
            entry[key] = current[key]
    return entry


def expected_requests(fixture_entry: dict[str, Any]) -> list[dict[str, Any]]:
    """Return the requests the current code must send for a fixture entry.

    Args:
        fixture_entry: One entry of the fixture.

    Returns:
        ``v2.requests`` when the requests changed by decision, otherwise the point A requests.
    """
    return fixture_entry["v2"].get("requests", fixture_entry.get("requests"))


def load_fixture() -> list[dict[str, Any]]:
    """Load the fixture entries.

    Returns:
        The entries in table order.
    """
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def write_fixture(entries: list[dict[str, Any]]) -> None:
    """Write the fixture with one scenario per line (readable diffs).

    Args:
        entries: Fixture entries.
    """
    lines = [json.dumps(entry, ensure_ascii=False, sort_keys=True) for entry in entries]
    FIXTURE.write_text("[\n" + ",\n".join(lines) + "\n]\n", encoding="utf-8")


def record_normalized() -> list[str]:
    """Record the ``v2`` part of every fixture entry, keeping the point A fields.

    Returns:
        Ids whose requests differ from point A without a declared ``requests_change``
        (the fixture is not written when this list is not empty).
    """
    entries = {entry["id"]: entry for entry in load_fixture()}
    undeclared = []
    for glpi in mocked_glpi():
        for scenario in SCENARIOS:
            # Scenarios created with the normalized contract have no point A fields
            entry = entries.setdefault(scenario["id"], {"id": scenario["id"], "call": scenario["call"],
                                                         "since": "v2"})
            current = run_normalized(scenario, glpi)
            if "requests" in entry:
                # Unchanged requests are not duplicated under v2
                if current["requests"] == entry["requests"]:
                    current.pop("requests")
                elif "requests_change" not in current:
                    undeclared.append(scenario["id"])
            entry["v2"] = current
    if not undeclared:
        write_fixture([entries[scenario["id"]] for scenario in SCENARIOS])
    return undeclared


def main(argv: list[str] | None = None) -> int:
    """Record the normalized part of the fixture.

    Args:
        argv: Command line arguments (defaults to ``sys.argv[1:]``).

    Returns:
        Process exit code.
    """
    args = sys.argv[1:] if argv is None else argv
    if "--normalized" not in args:
        print("point A was recorded with glpi-api (commit 58be2a7); use --normalized", file=sys.stderr)
        return 2
    undeclared = record_normalized()
    if undeclared:
        print("requests changed without requests_change: " + ", ".join(undeclared), file=sys.stderr)
        return 1
    print(f"{len(SCENARIOS)} scenarios recorded (v2) in {FIXTURE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
