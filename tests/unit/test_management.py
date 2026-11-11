"""Management models: sub-item methods, document upload/download and the safety of the download."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from glpi_api_hero import management as mg
from tests.conftest import GlpiMock

# (id, call, method, path, body input or None)
READS: list[tuple[str, Callable[[], Any], str]] = [
    ("softwarelicense-installations", lambda: mg.SoftwareLicense.get_installations(1),
     "SoftwareLicense/1/Item_SoftwareLicense"),
    ("supplier-contacts", lambda: mg.Supplier.get_contacts(2), "Supplier/2/Contact_Supplier"),
    ("supplier-contracts", lambda: mg.Supplier.get_contracts(2), "Supplier/2/Contract_Supplier"),
    ("contact-suppliers", lambda: mg.Contact.get_suppliers(3), "Contact/3/Contact_Supplier"),
    ("contract-items", lambda: mg.Contract.get_items(4), "Contract/4/Contract_Item"),
    ("contract-suppliers", lambda: mg.Contract.get_suppliers(4), "Contract/4/Contract_Supplier"),
    ("contract-costs", lambda: mg.Contract.get_costs(4), "Contract/4/ContractCost"),
    ("document-items", lambda: mg.Document.get_items(5), "Document/5/Document_Item"),
    ("certificate-items", lambda: mg.Certificate.get_items(6), "Certificate/6/Certificate_Item"),
    ("cluster-items", lambda: mg.Cluster.get_items(7), "Cluster/7/Item_Cluster"),
    ("domain-items", lambda: mg.Domain.get_items(8), "Domain/8/Domain_Item"),
    ("domain-records", lambda: mg.Domain.get_records(8), "Domain/8/DomainRecord"),
    ("appliance-items", lambda: mg.Appliance.get_items(9), "Appliance/9/Appliance_Item"),
    ("databaseinstance-databases", lambda: mg.DatabaseInstance.get_databases(10), "DatabaseInstance/10/Database"),
    ("contract-documents", lambda: mg.Contract.get_documents(4), "Contract/4/Document_Item"),
    ("line-contracts", lambda: mg.Line.get_contracts(4), "Line/4/Contract_Item"),
    ("domain-certificates", lambda: mg.Domain.get_certificates(8), "Domain/8/Certificate_Item"),
    ("cluster-appliances", lambda: mg.Cluster.get_appliances(7), "Cluster/7/Appliance_Item"),
    ("supplier-notes", lambda: mg.Supplier.get_notes(2), "Supplier/2/Notepad"),
    ("datacenter-logs", lambda: mg.Datacenter.get_logs(2), "Datacenter/2/Log"),
]


@pytest.mark.parametrize(("call", "path"), [(c, p) for _, c, p in READS], ids=[i for i, _, _ in READS])
def test_reads(session: GlpiMock, call: Callable[[], Any], path: str) -> None:
    """Each reader is one GET on the expected sub-item."""
    call()
    assert [(r["method"], r["path"]) for r in session.captured()] == [("GET", path)]


# (id, call, expected method, path, input)
WRITES: list[tuple[str, Callable[[], Any], str, str, dict[str, Any]]] = [
    ("contract-add-item", lambda: mg.Contract.add_item(4, "Computer", 3), "POST", "Contract_Item",
     {"contracts_id": 4, "itemtype": "Computer", "items_id": 3}),
    ("contract-delete-item", lambda: mg.Contract.delete_item(30), "DELETE", "Contract_Item", {"id": 30}),
    ("document-link-item", lambda: mg.Document.link_item(5, "Ticket", 8), "POST", "Document_Item",
     {"documents_id": 5, "itemtype": "Ticket", "items_id": 8}),
    ("domain-add-record", lambda: mg.Domain.add_record(8, {"name": "www", "type": 1}), "POST", "DomainRecord",
     {"name": "www", "type": 1, "domains_id": 8}),
    ("domain-update-record", lambda: mg.Domain.update_record(40, {"data": "x"}), "PUT", "DomainRecord",
     {"data": "x", "id": 40}),
    ("domain-delete-record", lambda: mg.Domain.delete_record(40), "DELETE", "DomainRecord", {"id": 40}),
    ("databaseinstance-add-database", lambda: mg.DatabaseInstance.add_database(10, {"name": "db"}), "POST",
     "Database", {"name": "db", "databaseinstances_id": 10}),
    ("databaseinstance-update-database", lambda: mg.DatabaseInstance.update_database(50, {"name": "x"}), "PUT",
     "Database", {"name": "x", "id": 50}),
    ("databaseinstance-delete-database", lambda: mg.DatabaseInstance.delete_database(50), "DELETE", "Database",
     {"id": 50}),
]


@pytest.mark.parametrize(("call", "method", "path", "expected"), [w[1:] for w in WRITES],
                         ids=[w[0] for w in WRITES])
def test_writes(session: GlpiMock, call: Callable[[], Any], method: str, path: str, expected: dict[str, Any]) -> None:
    """Writes bind the child to the parent with the column GLPI expects."""
    call()
    request = session.captured()[0]
    assert (request["method"], request["path"], request["body"]["input"][0]) == (method, path, expected)


def test_writes_do_not_modify_the_input(session: GlpiMock) -> None:
    """The caller dicts stay as they were."""
    record = {"name": "www"}
    mg.Domain.add_record(1, record)
    database = {"name": "db"}
    mg.DatabaseInstance.add_database(1, database)
    assert record == {"name": "www"}
    assert database == {"name": "db"}


def test_upload_streams_the_file(session: GlpiMock, tmp_path: Path) -> None:
    """The upload is a multipart request and returns the new id."""
    source = tmp_path / "contract.pdf"
    source.write_bytes(b"%PDF")
    session.override("POST", "Document", 201, {"id": 12, "message": ""})
    assert mg.Document.upload("Contract scan", source) == 12
    assert session.rsps.calls[0].request.headers["Content-Type"].startswith("multipart/form-data")


def test_upload_of_a_missing_file_fails_before_any_request(session: GlpiMock, tmp_path: Path) -> None:
    """A missing path is a ``FileNotFoundError`` and no request is sent."""
    with pytest.raises(FileNotFoundError):
        mg.Document.upload("x", tmp_path / "missing.pdf")
    with pytest.raises(FileNotFoundError):
        mg.Document.upload("x", tmp_path)
    assert session.captured() == []


@pytest.mark.parametrize(("header", "expected"), [
    ('attachment; filename="../../etc/passwd"', "passwd"),
    ('attachment; filename="..\\\\..\\\\win.ini"', "win.ini"),
    ('attachment; filename="/abs/path.txt"', "path.txt"),
    ('attachment; filename=".."', "document-9"),
    ('attachment; filename=""', "document-9"),
    ("attachment", "document-9"),
])
def test_download_sanitization(session: GlpiMock, tmp_path: Path, header: str, expected: str) -> None:
    """The stored name is reduced to a plain file name that stays inside the directory."""
    directory = tmp_path / "out"
    directory.mkdir()
    session.override("GET", "Document/9", 200, "data", headers={"Content-Disposition": header})
    target = mg.Document.download(9, directory)
    assert target == directory / expected
    assert target.read_text() == "data"
    assert sorted(path.name for path in tmp_path.iterdir()) == ["out"]


def test_download_sanitization_of_an_explicit_name(session: GlpiMock, tmp_path: Path) -> None:
    """A caller-given name is cleaned the same way."""
    directory = tmp_path / "out"
    directory.mkdir()
    session.override("GET", "Document/9", 200, "data")
    assert mg.Document.download(9, directory, "../../x.txt") == directory / "x.txt"
    assert (tmp_path / "x.txt").exists() is False


def test_download_sanitization_refuses_to_overwrite_and_leaves_the_file(session: GlpiMock, tmp_path: Path) -> None:
    """An existing file is kept unless ``overwrite=True``."""
    session.override("GET", "Document/9", 200, "new", headers={"Content-Disposition": 'attachment; filename="a.txt"'})
    (tmp_path / "a.txt").write_text("old")
    with pytest.raises(FileExistsError):
        mg.Document.download(9, tmp_path)
    assert (tmp_path / "a.txt").read_text() == "old"
    mg.Document.download(9, tmp_path, overwrite=True)
    assert (tmp_path / "a.txt").read_text() == "new"


def test_download_sanitization_rejects_a_symlink_out_of_the_directory(session: GlpiMock, tmp_path: Path) -> None:
    """A symlink named like the file cannot send the bytes elsewhere (``ValueError``)."""
    outside = tmp_path / "secret.txt"
    directory = tmp_path / "out"
    directory.mkdir()
    (directory / "a.txt").symlink_to(outside)
    session.override("GET", "Document/9", 200, "x", headers={"Content-Disposition": 'attachment; filename="a.txt"'})
    with pytest.raises(ValueError):
        mg.Document.download(9, directory, overwrite=True)
    assert not outside.exists()
