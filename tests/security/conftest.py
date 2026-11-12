"""Fixtures of the security tests: an open session on the GLPI simulator."""

from __future__ import annotations

from collections.abc import Iterator

import pytest

from glpi_api_hero import Glpi
from tests.conftest import APP_TOKEN, BASE_URL, USER_TOKEN, GlpiMock


@pytest.fixture
def session(glpi_mock: GlpiMock) -> Iterator[GlpiMock]:
    """Open a session on the simulator and forget the login request.

    Args:
        glpi_mock: Active GLPI simulator.

    Yields:
        The simulator, with no captured request.
    """
    Glpi.connect(BASE_URL, APP_TOKEN, user_token=USER_TOKEN)
    glpi_mock.reset_calls()
    yield glpi_mock
