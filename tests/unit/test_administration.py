"""Administration models: user, group, entity and profile."""

from __future__ import annotations

from glpi_api_hero.administration import Entity, Group, Profile, User
from tests.conftest import GlpiMock


def test_profile_users_and_user_emails(session: GlpiMock) -> None:
    """The extra readers address ``Profile_User`` and ``UserEmail``."""
    Profile.get_users(4)
    User.get_emails(3)
    assert [c["path"] for c in session.captured()] == ["Profile/4/Profile_User", "User/3/UserEmail"]


def test_entity_tree_lookups(session: GlpiMock) -> None:
    """Entity inherits the tree lookups (options 14 name, 13 parent)."""
    Entity.get_by_name("HQ")
    Entity.get_children(0)
    queries = [c["query"] for c in session.captured()]
    assert queries[0]["criteria[0][field]"] == "14"
    assert (queries[1]["criteria[0][field]"], queries[1]["criteria[0][value]"]) == ("13", "0")


def test_group_is_a_tree_with_notes_and_user_documents(session: GlpiMock) -> None:
    """Group keeps its own methods and gains the tree base; User gets the documents and certificates readers."""
    assert hasattr(Group, "get_roots") and hasattr(Group, "get_notes") and hasattr(Group, "get_users")
    User.get_documents(3)
    User.get_certificates(3)
    assert [c["path"] for c in session.captured()] == ["User/3/Document_Item", "User/3/Certificate_Item"]
