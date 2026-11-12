"""Constants shared by the models."""

from enum import Enum, IntEnum


class ActorType(IntEnum):
    """Role of a user or group in an ITIL object (value of the GLPI ``type`` field)."""

    REQUESTER = 1
    ASSIGNED = 2
    OBSERVER = 3


class ActorKind(str, Enum):
    """Kind of actor of an ITIL object (``StrEnum`` needs Python 3.11 and the minimum is 3.10)."""

    USER = "user"
    GROUP = "group"
    SUPPLIER = "supplier"


class LinkType(IntEnum):
    """Relation between two tickets (value of the ``link`` field of ``Ticket_Ticket``).

    ``CHILD`` means the first ticket is a child of the second (GLPI ``SON_OF``). GLPI stores ``PARENT``
    as the reverse ``CHILD`` row (columns swapped), so reads never return ``PARENT``.
    """

    LINKED = 1
    DUPLICATE = 2
    CHILD = 3
    PARENT = 4
