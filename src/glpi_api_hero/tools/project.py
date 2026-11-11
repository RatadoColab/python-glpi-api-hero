"""Projects (Tools > Projects)."""

from __future__ import annotations

from typing import Any

from glpi_api_hero.core.capabilities import HasContracts, HasDocuments, HasLogs, HasNotes


class Project(HasContracts, HasDocuments, HasNotes, HasLogs):
    """GLPI ``Project``."""

    @classmethod
    def get_tasks(cls, project_id: int, **params: Any) -> list[dict[str, Any]]:
        """Return the tasks of the project (``ProjectTask``).

        Args:
            project_id: Parent id.
            **params: Extra API parameters.

        Returns:
            The rows.
        """
        return cls.get_sub_items(project_id, "ProjectTask", **params)

    @classmethod
    def add_task(cls, project_id: int, data: dict[str, Any]) -> int:
        """Add a task of the project (``ProjectTask``).

        Args:
            project_id: Parent id.
            data: Fields; not modified.

        Returns:
            The new id.
        """
        return cls._for("ProjectTask").add({**data, "projects_id": project_id})

    @classmethod
    def update_task(cls, task_id: int, data: dict[str, Any]) -> None:
        """Update a task of the project.

        Args:
            task_id: Id of the row.
            data: Fields to change; not modified.
        """
        cls._for("ProjectTask").update(task_id, data)

    @classmethod
    def delete_task(cls, task_id: int) -> None:
        """Delete a task of the project.

        Args:
            task_id: Id of the row.
        """
        cls._for("ProjectTask").delete(task_id)

    @classmethod
    def get_team(cls, project_id: int, **params: Any) -> list[dict[str, Any]]:
        """Return the team of the project (``ProjectTeam``).

        Args:
            project_id: Parent id.
            **params: Extra API parameters.

        Returns:
            The rows.
        """
        return cls.get_sub_items(project_id, "ProjectTeam", **params)

    @classmethod
    def add_team_member(cls, project_id: int, itemtype: str, items_id: int) -> int:
        """Add a member to the project team (``ProjectTeam``).

        Args:
            project_id: Project id.
            itemtype: ``User``, ``Group``, ``Supplier`` or ``Contact``.
            items_id: Id of the member.

        Returns:
            The id of the team row.
        """
        return cls._for("ProjectTeam").add({"projects_id": project_id, "itemtype": itemtype, "items_id": items_id})

    @classmethod
    def delete_team_member(cls, team_id: int) -> None:
        """Remove a member from the project team.

        Args:
            team_id: Id of the ``ProjectTeam`` row (not the id of the user or group).
        """
        cls._for("ProjectTeam").delete(team_id)

    @classmethod
    def get_items(cls, project_id: int, **params: Any) -> list[dict[str, Any]]:
        """Return the items linked to the project (``Item_Project``).

        Args:
            project_id: Parent id.
            **params: Extra API parameters.

        Returns:
            The rows.
        """
        return cls.get_sub_items(project_id, "Item_Project", **params)

    @classmethod
    def get_costs(cls, project_id: int, **params: Any) -> list[dict[str, Any]]:
        """Return the costs of the project (``ProjectCost``).

        Args:
            project_id: Parent id.
            **params: Extra API parameters.

        Returns:
            The rows.
        """
        return cls.get_sub_items(project_id, "ProjectCost", **params)

    @classmethod
    def get_itil_objects(cls, project_id: int, **params: Any) -> list[dict[str, Any]]:
        """Return the tickets, changes and problems of the project (``Itil_Project``).

        Args:
            project_id: Parent id.
            **params: Extra API parameters.

        Returns:
            The rows.
        """
        return cls.get_sub_items(project_id, "Itil_Project", **params)
