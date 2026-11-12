"""Reservable items (Tools > Reservations)."""

from __future__ import annotations

from typing import Any

from glpi_api_hero.core.common_dbtm import CommonDBTM


class ReservationItem(CommonDBTM):
    """GLPI ``ReservationItem``."""

    @classmethod
    def get_reservations(cls, reservationitem_id: int, **params: Any) -> list[dict[str, Any]]:
        """Return the reservations of the item (``Reservation``).

        Args:
            reservationitem_id: Parent id.
            **params: Extra API parameters.

        Returns:
            The rows.
        """
        return cls.get_sub_items(reservationitem_id, "Reservation", **params)

    @classmethod
    def add_reservation(cls, reservationitem_id: int, data: dict[str, Any]) -> int:
        """Add a reservation of the item (``Reservation``).

        Args:
            reservationitem_id: Parent id.
            data: Fields; not modified.

        Returns:
            The new id.
        """
        return cls._for("Reservation").add({**data, "reservationitems_id": reservationitem_id})

    @classmethod
    def delete_reservation(cls, reservation_id: int) -> None:
        """Delete a reservation of the item.

        Args:
            reservation_id: Id of the row.
        """
        cls._for("Reservation").delete(reservation_id)
