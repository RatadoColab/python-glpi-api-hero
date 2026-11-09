"""HTTP contract characterization: current requests and results must match the fixture."""

from __future__ import annotations

import inspect
import json
from typing import Any

import pytest

from tests.characterization.record import FIXTURE, resolve_class, run_scenario
from tests.characterization.scenarios import SCENARIOS

# Classes whose public methods must all be characterized
CHARACTERIZED = ("CommonDBTM", "ApiCommunication", "User", "Group", "Computer", "Location", "Ticket")


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
        The main call plus the calls of its steps.
    """
    return [scenario["call"], *(step["call"] for step in scenario.get("steps", []))]


def test_scenario_ids_are_unique() -> None:
    """Scenario ids identify fixture entries, so they must be unique."""
    ids = [scenario["id"] for scenario in SCENARIOS]
    assert len(ids) == len(set(ids))


def test_fixture_matches_scenario_table() -> None:
    """The fixture has exactly one entry per scenario."""
    assert sorted(_fixture()) == sorted(scenario["id"] for scenario in SCENARIOS)


@pytest.mark.parametrize("scenario", SCENARIOS, ids=[s["id"] for s in SCENARIOS])
def test_http_contract(scenario: dict[str, Any], glpi_mock: Any) -> None:
    """Requests sent and the returned value (or raised error) match the recording.

    Args:
        scenario: Scenario under test.
        glpi_mock: Active GLPI simulator.
    """
    expected = _fixture()[scenario["id"]]
    actual = json.loads(json.dumps(run_scenario(scenario, glpi_mock), sort_keys=True))
    assert actual["requests"] == expected["requests"]
    assert actual.get("returns") == expected.get("returns")
    assert actual.get("raises") == expected.get("raises")
    assert actual == expected


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
