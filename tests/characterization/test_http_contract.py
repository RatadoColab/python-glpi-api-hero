"""HTTP contract characterization: current requests and results must match the fixture."""

from __future__ import annotations

import functools
import inspect
import json
from typing import Any

import pytest

from tests.characterization.record import FIXTURE, expected_requests, resolve_class, run_normalized
from tests.characterization.scenarios import SCENARIOS, normalized

# Classes whose public methods must all be characterized
CHARACTERIZED = ("CommonDBTM", "ApiCommunication", "User", "Group", "Computer", "Location", "Ticket",
                 "TicketDashboard")


@functools.cache
def _fixture() -> dict[str, dict[str, Any]]:
    """Load the recorded fixture indexed by scenario id.

    Returns:
        Mapping ``id`` → fixture entry.
    """
    entries = json.loads(FIXTURE.read_text(encoding="utf-8"))
    return {entry["id"]: entry for entry in entries}


def _calls(scenario: dict[str, Any]) -> list[str]:
    """List every ``Class.method`` invoked by a scenario.

    Args:
        scenario: Scenario dict.

    Returns:
        The calls of its steps, or the single ``call`` when there are no steps.
    """
    current = normalized(scenario)
    if "steps" in current:
        return [step["call"] for step in current["steps"]]
    return [current["call"]]


def test_scenario_ids_are_unique() -> None:
    """Scenario ids identify fixture entries, so they must be unique."""
    ids = [scenario["id"] for scenario in SCENARIOS]
    assert len(ids) == len(set(ids))


def test_call_is_the_last_step() -> None:
    """``call`` names what runs: with ``steps`` it must be the last step."""
    current = [normalized(s) for s in SCENARIOS]
    mismatched = [s["id"] for s in current if "steps" in s and s["steps"][-1]["call"] != s["call"]]
    assert mismatched == []


def test_fixture_matches_scenario_table() -> None:
    """The fixture has exactly one entry per scenario."""
    assert sorted(_fixture()) == sorted(scenario["id"] for scenario in SCENARIOS)


@pytest.mark.parametrize("scenario", SCENARIOS, ids=[s["id"] for s in SCENARIOS])
def test_http_contract(scenario: dict[str, Any], glpi_mock: Any) -> None:
    """Requests sent equal point A (unless changed by a recorded decision) and results match ``v2``.

    Args:
        scenario: Scenario under test.
        glpi_mock: Active GLPI simulator.
    """
    expected = _fixture()[scenario["id"]]
    actual = json.loads(json.dumps(run_normalized(scenario, glpi_mock), sort_keys=True))
    assert actual.pop("requests") == expected_requests(expected)
    v2 = {key: value for key, value in expected["v2"].items() if key != "requests"}
    assert actual.get("returns") == v2.get("returns")
    assert actual.get("raises") == v2.get("raises")
    assert actual == v2


def test_coverage_of_public_methods() -> None:
    """Every public class/static method of the characterized classes has a scenario."""
    called = [call.split(".", 1) for scenario in SCENARIOS for call in _calls(scenario)]
    missing = []
    for owner_name in CHARACTERIZED:
        owner = resolve_class(owner_name)
        for name, attr in vars(owner).items():
            # Only public class-level callables are part of the API surface
            if name.startswith("_") or not isinstance(attr, (classmethod, staticmethod)):
                continue
            covered = any(
                method == name and inspect.isclass(resolve_class(cls)) and issubclass(resolve_class(cls), owner)
                for cls, method in called
            )
            if not covered:
                missing.append(f"{owner_name}.{name}")
    assert missing == []
