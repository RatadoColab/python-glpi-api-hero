"""Constants shared by the models."""

from enum import IntEnum


class ActorType(IntEnum):
    """Role of a user or group in a ticket (value of the GLPI ``type`` field)."""

    REQUESTER = 1
    ASSIGNED = 2
    OBSERVER = 3
