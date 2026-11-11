# Management

`glpi_api_hero.management`: `SoftwareLicense`, `Budget`, `Supplier`, `Contact`, `Contract`, `Document`, `Line`,
`Certificate`, `Datacenter`, `Cluster`, `Domain`, `Appliance`, `DatabaseInstance`.

| Model | Specific methods |
|---|---|
| `SoftwareLicense` | `get_installations` |
| `Supplier` | `get_contacts`, `get_contracts` |
| `Contact` | `get_suppliers` |
| `Contract` | `get_items`, `get_suppliers`, `get_costs`, `add_item`, `delete_item` |
| `Document` | `upload`, `download`, `get_items`, `link_item` |
| `Certificate`, `Cluster`, `Appliance` | `get_items` |
| `Domain` | `get_items`, `get_records`, `add_record`, `update_record`, `delete_record` |
| `DatabaseInstance` | `get_databases`, `add_database`, `update_database`, `delete_database` |

Capability readers (`get_documents`, `get_contracts`, `get_infocom`, `get_tickets`...) exist where GLPI allows them.

```python
from glpi_api_hero.management import Document

document_id = Document.upload("Contract scan", "/tmp/contract.pdf")
path = Document.download(document_id, "/tmp/out")                   # owner-only file
Document.download(document_id, "/tmp/out", overwrite=True)          # replace an existing file
```

`Document.upload` raises `FileNotFoundError` before any request when the file is missing. `download` keeps only a
plain file name, never writes outside the directory (`ValueError`) and refuses to overwrite by default
(`FileExistsError`).
