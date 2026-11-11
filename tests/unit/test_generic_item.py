"""GenericItem.of(): class factory for any itemtype."""

from __future__ import annotations

import pytest

from glpi_api_hero import CommonDBTM, GenericItem
from glpi_api_hero.assets import Computer
from tests.conftest import GlpiMock


def test_of_returns_a_commondbtm_subclass_bound_to_the_itemtype() -> None:
    """The class has the itemtype, a readable name and a readable repr."""
    line = GenericItem.of("Line")
    assert issubclass(line, CommonDBTM)
    assert line.get_class_name() == "Line"
    assert (line.__name__, line.__qualname__) == ("GenericLine", "GenericLine")
    assert repr(line) == "<GenericItem 'Line'>"


def test_of_is_cached_per_itemtype() -> None:
    """Two calls with the same itemtype return the same class object."""
    assert GenericItem.of("Line") is GenericItem.of("Line")
    assert GenericItem.of("Line") is not GenericItem.of("Cable")


def test_of_never_returns_the_typed_model() -> None:
    """``of("Computer")`` is a dynamic class, not ``assets.Computer``."""
    assert GenericItem.of("Computer") is not Computer
    assert GenericItem.of("Computer").get_class_name() == "Computer"


@pytest.mark.parametrize("name", ["", None, 3, "../x", "Computer/1", "Computer?x=1", "Line\n", " Line", "1Line",
                                  "Glpi\\\\Socket", "Glpi\\", "\\Socket", "a b"])
def test_of_rejects_invalid_names(name: object) -> None:
    """Invalid itemtypes fail with ``ValueError`` (before any request).

    Args:
        name: Invalid value.
    """
    with pytest.raises(ValueError, match="invalid GLPI itemtype"):
        GenericItem.of(name)  # type: ignore[arg-type]


def test_namespaced_itemtypes_are_accepted_and_encoded(session: GlpiMock) -> None:
    """``Glpi\\Socket`` is valid and travels percent-encoded in the URL.

    Args:
        session: Simulator with an open session.
    """
    socket = GenericItem.of("Glpi\\Socket")
    assert (socket.__name__, socket.get_class_name()) == ("GenericGlpiSocket", "Glpi\\Socket")
    session.reset_calls()
    socket.get_all()
    assert session.rsps.calls[0].request.url.split("?")[0].endswith("/Glpi%5CSocket")


def test_generated_classes_work_like_models(session: GlpiMock) -> None:
    """A generated class performs the generic CRUD on its itemtype.

    Args:
        session: Simulator with an open session.
    """
    line = GenericItem.of("Line")
    session.reset_calls()
    assert isinstance(line.add({"name": "x"}), int)
    assert [request["path"] for request in session.captured()] == ["Line"]


def test_classes_are_not_instantiable() -> None:
    """Models are used through class methods only."""
    with pytest.raises(TypeError, match="not instantiable"):
        GenericItem()
    with pytest.raises(TypeError, match="not instantiable"):
        GenericItem.of("Line")()


def test_invalid_name_sends_no_request(session: GlpiMock) -> None:
    """Validation happens before the transport.

    Args:
        session: Simulator with an open session.
    """
    session.reset_calls()
    with pytest.raises(ValueError, match="invalid GLPI itemtype"):
        GenericItem.of("../x").get_all()
    assert session.captured() == []


def test_concurrent_first_calls_share_one_class() -> None:
    """Threads asking for a new itemtype at the same time get the same class object."""
    import threading

    results: list[type] = []
    barrier = threading.Barrier(8)

    def worker() -> None:
        """Wait for the others, then ask for the class."""
        barrier.wait()
        results.append(GenericItem.of("PluginRaceTest"))

    threads = [threading.Thread(target=worker) for _ in range(8)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert len({id(cls) for cls in results}) == 1
