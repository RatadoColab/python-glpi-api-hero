"""Models of the Management menu."""

from glpi_api_hero.management.appliance import Appliance
from glpi_api_hero.management.budget import Budget
from glpi_api_hero.management.certificate import Certificate
from glpi_api_hero.management.cluster import Cluster
from glpi_api_hero.management.contact import Contact
from glpi_api_hero.management.contract import Contract
from glpi_api_hero.management.database_instance import DatabaseInstance
from glpi_api_hero.management.datacenter import Datacenter
from glpi_api_hero.management.document import Document
from glpi_api_hero.management.domain import Domain
from glpi_api_hero.management.line import Line
from glpi_api_hero.management.software_license import SoftwareLicense
from glpi_api_hero.management.supplier import Supplier

__all__ = [
    "Appliance",
    "Budget",
    "Certificate",
    "Cluster",
    "Contact",
    "Contract",
    "DatabaseInstance",
    "Datacenter",
    "Document",
    "Domain",
    "Line",
    "SoftwareLicense",
    "Supplier",
]
