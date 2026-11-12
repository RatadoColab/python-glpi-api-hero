"""Regression tests for the findings of the final release review (phase 12)."""

from __future__ import annotations

import pytest

from glpi_api_hero import Glpi
from glpi_api_hero.administration import Group, User
from glpi_api_hero.assets import Computer, Software
from glpi_api_hero.core.constants import ActorType
from glpi_api_hero.core.legacy_rest import LegacyRestConnector
from glpi_api_hero.dropdowns import Location
from tests.conftest import APP_TOKEN, BASE_URL, USER_TOKEN, GlpiMock


def test_requests_ask_for_unsanitized_content(session: GlpiMock) -> None:
    """Every request after the login asks GLPI for raw text instead of HTML entities.

    Args:
        session: Simulator with an open session.
    """
    connector = Glpi.connector()
    assert isinstance(connector, LegacyRestConnector)
    assert connector._http.headers["X-GLPI-Sanitized-Content"] == "false"


def test_search_rows_come_back_decoded(session: GlpiMock) -> None:
    """The search engine answers with HTML entities; the rows reach the caller as plain text.

    Args:
        session: Simulator with an open session.
    """
    body = {"totalcount": 1, "count": 1, "data": [
        {"1": "R&#38;D &#60;b&#62;", "21": "&#60;p&#62;a &#38; b&#60;/p&#62;", "2": 7, "80": ["x &#38; y"]}]}
    session.override("GET", "search/Computer", 200, body)
    assert Computer.search(None) == [{"1": "R&D <b>", "21": "<p>a & b</p>", "2": 7, "80": ["x & y"]}]
    assert Glpi.connector().search_body("Computer")["data"][0]["21"] == "<p>a & b</p>"


def test_range_beyond_total_returns_empty_lists(session: GlpiMock) -> None:
    """A range that starts after the last row is an empty page, not an error.

    Args:
        session: Simulator with an open session.
    """
    body = ["ERROR_RANGE_EXCEED_TOTAL", "Provided range exceed total count of data"]
    session.override("GET", "Computer", 400, body)
    session.override("GET", "search/Computer", 400, body)
    session.override("GET", "Computer/1/Item_Disk", 400, body)
    assert Computer.get_all(range="500-549") == []
    assert Computer.search(None, range="500-549") == []
    assert Computer.get_sub_items(1, "Item_Disk", range="500-549") == []


def test_other_bad_requests_still_raise(session: GlpiMock) -> None:
    """Only the exceeded range is turned into an empty page.

    Args:
        session: Simulator with an open session.
    """
    from glpi_api_hero.exceptions import BadRequestError

    session.override("GET", "Computer", 400, ["ERROR_BAD_ARRAY", "bad"])
    with pytest.raises(BadRequestError):
        Computer.get_all()


def test_nan_payload_is_a_value_error(session: GlpiMock) -> None:
    """A payload that cannot be encoded as JSON is a caller error, not a connection failure.

    Args:
        session: Simulator with an open session.
    """
    with pytest.raises(ValueError, match="not valid JSON"):
        Location.add({"name": float("nan")})


@pytest.mark.parametrize(("call", "expected"), [
    (lambda: User.get_by_username("glpi"), "^glpi$"),
    (lambda: User.get_by_email("a@b.test"), "^a@b.test$"),
    (lambda: Group.get_by_name("Support"), "^Support$"),
])
def test_exact_lookups_use_the_anchored_text_match(session: GlpiMock, call, expected: str) -> None:
    """Link fields compare ``equals`` with the item id, so exact lookups use ``contains`` with anchors.

    Args:
        session: Simulator with an open session.
        call: Lookup under test.
        expected: Expected criterion value.
    """
    call()
    query = session.captured()[-1]["query"]
    assert query["criteria[0][searchtype]"] == "contains"
    assert query["criteria[0][value]"] == expected


@pytest.mark.parametrize("call", [
    lambda: User.get_tickets(2, 9),
    lambda: Group.get_tickets(5, 9),
])
def test_unknown_actor_type_raises(session: GlpiMock, call) -> None:
    """An unknown role raises ``ValueError`` before any request.

    Args:
        session: Simulator with an open session.
        call: Search under test.
    """
    with pytest.raises(ValueError, match="not a valid ActorType"):
        call()
    assert session.captured() == []
    assert ActorType.ASSIGNED in tuple(ActorType)


def test_software_installations_read_all_versions(session: GlpiMock) -> None:
    """The versions are read with a wide range, so versions beyond the first page are not dropped.

    Args:
        session: Simulator with an open session.
    """
    Software.get_installations(7)
    first = session.captured()[0]
    assert first["path"] == "Software/7/SoftwareVersion"
    assert first["query"]["range"] == "0-9999"


def test_logout_failure_after_a_successful_block_keeps_the_result(glpi_mock: GlpiMock) -> None:
    """The value computed inside the block is not lost when the logout fails.

    Args:
        glpi_mock: Active GLPI simulator.
    """
    glpi_mock.override("GET", "killSession", 500, ["ERROR_UNKNOWN", "boom"])

    def work() -> str:
        """Return a value from inside the session block.

        Returns:
            A marker string.
        """
        with Glpi.session(BASE_URL, APP_TOKEN, user_token=USER_TOKEN):
            return "done"

    assert work() == "done"


def test_update_from_list_updates_a_record_repeated_in_the_batch(session: GlpiMock) -> None:
    """A location created earlier in the batch is matched (and updated) by a later record with the same name.

    Args:
        session: Simulator with an open session.
    """
    results = Location.update_from_list([{"name": "zz-batch-A"}, {"name": "zz-batch-A", "comment": "x"}])
    assert isinstance(results[0], int)
    assert results[1] is None
    methods = [request["method"] for request in session.captured()]
    assert methods.count("POST") == 1
    assert methods.count("PUT") == 1
