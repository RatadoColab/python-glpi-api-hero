"""Characterization scenarios: every public method of the current library.

Each scenario describes one call (or a short sequence of ``steps``) and the
simulated answers it needs. The recorded HTTP requests and the result are kept in
``fixtures/requests.json`` and act as the oracle of the transport refactoring.

Scenario keys:
    id: Unique, stable identifier.
    call: ``Class.method`` executed (the last step when ``steps`` is given).
    args / kwargs: Call arguments. Strings starting with ``@mapper:`` or ``@glpi:``
        are resolved at run time (see ``record.resolve``).
    session: ``"user_token"`` (default), ``"basic"`` or ``None`` (no session opened
        before the capture starts).
    steps: Optional list of ``{"call", "args", "kwargs"}`` run in order and captured.
    responses: Optional endpoint overrides (``method``, ``path``, ``status``, ``body``,
        ``headers``, ``error``).
    state: When true, the session state after the call is recorded.
    since: ``"v2"`` for scenarios of methods created by the normalized contract
        (no point A recording).
    known_bug: Description of a known bug recorded as it behaves today.
"""

from __future__ import annotations

from typing import Any

from tests.conftest import APP_TOKEN, BASE_URL, PASSWORD, USER_TOKEN, USERNAME


def upper_mapper(record: dict[str, Any]) -> dict[str, Any]:
    """Map a source record into GLPI Location fields (test mapper).

    Args:
        record: Source record with ``label`` and ``ref`` keys.

    Returns:
        Dict with GLPI ``name``, ``code`` and ``comment`` fields.
    """
    return {"name": record["label"].upper(), "code": record["ref"], "comment": "mapped"}


MAPPERS = {"upper": upper_mapper}

# Existing locations used by the updateFromList scenarios
_EXISTING_LOCATIONS = [
    {"id": 7, "name": "Building A", "code": "A01", "entities_id": 0},
    {"id": 8, "name": "Building B", "code": "", "entities_id": 0},
]

_ERR_401 = ["ERROR_SESSION_TOKEN_INVALID", "session_token seems invalid"]
_ERR_400 = ["ERROR_BAD_ARRAY", "input parameter must be an array of objects"]


def _session_steps(**connection: Any) -> list[dict[str, Any]]:
    """Build the steps that configure and open a session.

    Args:
        **connection: Extra keyword arguments for ``setConnectionParameters``.

    Returns:
        Steps for ``setConnectionParameters`` followed by ``initSession``.
    """
    return [
        {"call": "ApiCommunication.setConnectionParameters", "args": [BASE_URL, APP_TOKEN],
         "kwargs": connection},
        {"call": "ApiCommunication.initSession"},
    ]


def _sub(cls: str, method: str, item_id: int, **kwargs: Any) -> dict[str, Any]:
    """Build a scenario for a model method that reads sub-items.

    Args:
        cls: Model class name.
        method: Method name.
        item_id: Parent id.
        **kwargs: Extra keyword arguments.

    Returns:
        The scenario dict.
    """
    return {"id": f"{cls.lower()}-{method.lower()}", "call": f"{cls}.{method}",
            "args": [item_id], "kwargs": kwargs}


SCENARIOS: list[dict[str, Any]] = [
    # ------------------------------------------------------------------ session
    {"id": "session-set-connection-parameters", "call": "ApiCommunication.setConnectionParameters",
     "args": [BASE_URL, APP_TOKEN], "kwargs": {"usertoken": USER_TOKEN}, "session": None, "state": True,
     "known_bug": "user token stored under the misspelled key 'usertooken'"},
    {"id": "session-init-user-token", "call": "ApiCommunication.initSession", "session": None,
     "steps": _session_steps(usertoken=USER_TOKEN),
     "known_bug": "user token is not sent: Authorization header is 'user_token ' (empty token)"},
    {"id": "session-init-basic-auth", "call": "ApiCommunication.initSession", "session": None,
     "steps": _session_steps(user=USERNAME, passwd=PASSWORD)},
    {"id": "session-init-idempotent", "call": "ApiCommunication.initSession", "session": None,
     "steps": [*_session_steps(user=USERNAME, passwd=PASSWORD), {"call": "ApiCommunication.initSession"}]},
    {"id": "session-init-401", "call": "ApiCommunication.initSession", "session": None,
     "steps": _session_steps(user=USERNAME, passwd=PASSWORD),
     "responses": [{"method": "GET", "path": "initSession", "status": 401,
                    "body": ["ERROR_GLPI_LOGIN", "Incorrect username or password"]}]},
    {"id": "session-init-connection-error", "call": "ApiCommunication.initSession", "session": None,
     "steps": _session_steps(user=USERNAME, passwd=PASSWORD),
     "responses": [{"method": "GET", "path": "initSession", "error": "connection"}]},
    {"id": "session-init-insecure-default", "call": "ApiCommunication.getConn", "session": None,
     "steps": [*_session_steps(user=USERNAME, passwd=PASSWORD), {"call": "ApiCommunication.getConn"}],
     "inspect": "session_verify",
     "known_bug": "TLS certificate verification disabled by default (verify_certs=False)"},
    {"id": "session-set-profile-entity", "call": "ApiCommunication.setProfileEntity", "args": [4, 1]},
    {"id": "session-set-profile-entity-unchanged", "call": "ApiCommunication.setProfileEntity",
     "steps": [{"call": "ApiCommunication.setProfileEntity", "args": [4, 1]},
               {"call": "ApiCommunication.setProfileEntity", "args": [4, 1]}]},
    {"id": "session-set-profile-entity-recursion-change", "call": "ApiCommunication.setProfileEntity",
     "steps": [{"call": "ApiCommunication.setProfileEntity", "args": [4, 1]},
               {"call": "ApiCommunication.setProfileEntity", "args": [4, 1], "kwargs": {"is_recursive": False}}]},
    {"id": "session-set-profile-entity-404", "call": "ApiCommunication.setProfileEntity", "args": [99, 0],
     "responses": [{"method": "POST", "path": "changeActiveProfile", "status": 404,
                    "body": ["ERROR_ITEM_NOT_FOUND", "Item not found"]}],
     "known_bug": "glpi_api.GLPIError leaks without mapping to a project exception"},
    {"id": "session-set-profile-entity-without-parameters", "call": "ApiCommunication.setProfileEntity",
     "args": [4, 0], "session": None, "message": "type_only"},
    {"id": "session-get-logged-user", "call": "ApiCommunication.getLoggedUser",
     "known_bug": "calls the missing ApiCommunication.get_item (AttributeError)"},
    {"id": "session-get-conn", "call": "ApiCommunication.getConn"},
    {"id": "session-get-conn-none", "call": "ApiCommunication.getConn", "session": None},
    {"id": "session-kill", "call": "ApiCommunication.killSession", "state": True},
    {"id": "session-kill-without-session", "call": "ApiCommunication.killSession", "session": None},
    {"id": "session-kill-401", "call": "ApiCommunication.killSession",
     "responses": [{"method": "GET", "path": "killSession", "status": 401, "body": _ERR_401}]},
    {"id": "session-call-get-config", "call": "ApiCommunication.call", "args": ["@glpi:get_config"]},
    {"id": "session-call-429", "call": "ApiCommunication.call", "args": ["@glpi:get_config"],
     "responses": [{"method": "GET", "path": "getGlpiConfig", "status": 429, "body": "Too Many Requests"}]},
    # --------------------------------------------------------------- CommonDBTM
    {"id": "commondbtm-get-class-name", "call": "Location.get_class_name", "session": None},
    {"id": "commondbtm-get-class-name-override", "call": "Actor.get_class_name", "session": None},
    {"id": "commondbtm-add-one", "call": "Location.add", "args": [{"name": "loc-a"}]},
    {"id": "commondbtm-add-many", "call": "Location.add", "args": [{"name": "loc-a"}, {"name": "loc-b"}]},
    {"id": "commondbtm-add-207", "call": "Location.add", "args": [{"name": "loc-a"}, {"name": "loc-a"}],
     "responses": [{"method": "POST", "path": "Location", "status": 207,
                    "body": ["ERROR_GLPI_PARTIAL_ADD",
                             [{"id": 101, "message": ""},
                              {"id": False, "message": "Duplicate entry"}]]}]},
    {"id": "commondbtm-add-400", "call": "Location.add", "args": [{"name": "loc-a"}],
     "responses": [{"method": "POST", "path": "Location", "status": 400, "body": _ERR_400}]},
    {"id": "commondbtm-add-401", "call": "Location.add", "args": [{"name": "loc-a"}],
     "responses": [{"method": "POST", "path": "Location", "status": 401, "body": _ERR_401}]},
    {"id": "commondbtm-add-connection-error", "call": "Location.add", "args": [{"name": "loc-a"}],
     "responses": [{"method": "POST", "path": "Location", "error": "connection"}]},
    {"id": "commondbtm-update-one", "call": "Location.update", "args": [{"id": 7, "name": "loc-x"}]},
    {"id": "commondbtm-update-many", "call": "Location.update",
     "args": [{"id": 7, "name": "loc-x"}, {"id": 8, "name": "loc-y"}]},
    {"id": "commondbtm-update-207", "call": "Location.update",
     "args": [{"id": 7, "name": "loc-x"}, {"id": 999, "name": "loc-y"}],
     "responses": [{"method": "PUT", "path": "Location", "status": 207,
                    "body": ["ERROR_GLPI_PARTIAL_UPDATE",
                             [{"7": True, "message": ""}, {"999": False, "message": "Item not found"}]]}]},
    {"id": "commondbtm-delete-one", "call": "Location.delete", "args": [{"id": 7}]},
    {"id": "commondbtm-delete-many", "call": "Location.delete", "args": [{"id": 7}, {"id": 8}]},
    {"id": "commondbtm-delete-force-purge", "call": "Location.delete", "args": [{"id": 7}],
     "kwargs": {"force_purge": True}},
    {"id": "commondbtm-delete-error-glpi-delete", "call": "Location.delete", "args": [{"id": 999}],
     "responses": [{"method": "DELETE", "path": "Location", "status": 400,
                    "body": ["ERROR_GLPI_DELETE", [{"999": False, "message": "Item not found"}]]}],
     "known_bug": "ERROR_GLPI_DELETE returns the per-item list instead of raising"},
    {"id": "commondbtm-delete-400", "call": "Location.delete", "args": [{"id": 7}],
     "responses": [{"method": "DELETE", "path": "Location", "status": 400, "body": _ERR_400}]},
    {"id": "commondbtm-get", "call": "Location.get", "args": [7]},
    {"id": "commondbtm-get-kwargs", "call": "Location.get", "args": [7],
     "kwargs": {"expand_dropdowns": True, "with_logs": False}},
    {"id": "commondbtm-get-404", "call": "Location.get", "args": [999],
     "responses": [{"method": "GET", "path": "Location/999", "status": 404,
                    "body": ["ERROR_ITEM_NOT_FOUND", "Item not found"]}]},
    {"id": "commondbtm-get-429", "call": "Location.get", "args": [7],
     "responses": [{"method": "GET", "path": "Location/7", "status": 429, "body": "Too Many Requests"}]},
    {"id": "commondbtm-get-without-session", "call": "Location.get", "args": [7], "session": None},
    {"id": "commondbtm-get-all-items", "call": "Location.get_all_items"},
    {"id": "commondbtm-get-all-items-range-sort", "call": "Location.get_all_items",
     "kwargs": {"range": "0-49", "sort": 1, "order": "DESC", "is_deleted": False}},
    {"id": "commondbtm-get-all-items-206", "call": "Location.get_all_items", "kwargs": {"range": "0-0"},
     "responses": [{"method": "GET", "path": "Location", "status": 206,
                    "body": [{"id": 1, "name": "Location-1"}], "headers": {"Content-Range": "0-0/2"}}]},
    {"id": "commondbtm-get-all-items-searchtext", "call": "Location.get_all_items",
     "kwargs": {"searchText": {"name": "Build"}}},
    {"id": "commondbtm-get-sub-items", "call": "Computer.get_sub_items", "args": [3, "NetworkPort"]},
    {"id": "commondbtm-get-sub-items-kwargs", "call": "Computer.get_sub_items", "args": [3, "Log"],
     "kwargs": {"range": "0-9", "expand_dropdowns": True}},
    {"id": "commondbtm-search-criteria-id", "call": "Computer.search",
     "kwargs": {"criteria": [{"field": 1, "searchtype": "contains", "value": "pc"}]}},
    {"id": "commondbtm-search-criteria-uid", "call": "Computer.search",
     "kwargs": {"criteria": [{"field": "serial", "searchtype": "equals", "value": "SN1"}]}},
    {"id": "commondbtm-search-forcedisplay", "call": "Computer.search",
     "kwargs": {"criteria": [{"field": 1, "searchtype": "contains", "value": "pc"}],
                "forcedisplay": [1, "Entity.completename"]}},
    {"id": "commondbtm-search-range", "call": "Computer.search",
     "kwargs": {"criteria": [{"field": 1, "searchtype": "contains", "value": "pc"}], "range": "0-9",
                "sort": 1, "order": "ASC"}},
    {"id": "commondbtm-search-quote", "call": "User.search",
     "kwargs": {"criteria": [{"field": 1, "searchtype": "equals", "value": "o'brien"}]}},
    {"id": "commondbtm-search-nested-and-meta", "call": "Computer.search",
     "kwargs": {"criteria": [{"link": "AND", "criteria": [{"field": 1, "searchtype": "contains", "value": "a"},
                                                          {"link": "OR", "field": 5, "searchtype": "contains",
                                                           "value": "b"}]}],
                "metacriteria": [{"link": "AND", "itemtype": "Monitor", "field": 1,
                                  "searchtype": "contains", "value": "m"}]}},
    {"id": "commondbtm-search-206", "call": "Computer.search",
     "kwargs": {"criteria": [{"field": 1, "searchtype": "contains", "value": "pc"}], "range": "0-0"},
     "responses": [{"method": "GET", "path": "search/Computer", "status": 206,
                    "body": {"totalcount": 5, "count": 1, "data": [{"1": "pc-1", "2": 1}]},
                    "headers": {"Content-Range": "0-0/5"}}]},
    {"id": "commondbtm-search-empty", "call": "Computer.search",
     "kwargs": {"criteria": [{"field": 1, "searchtype": "equals", "value": "none"}]},
     "responses": [{"method": "GET", "path": "search/Computer", "status": 200,
                    "body": {"totalcount": 0, "count": 0}}]},
    {"id": "commondbtm-search-400", "call": "Computer.search",
     "kwargs": {"criteria": [{"field": 1, "searchtype": "bad", "value": "pc"}]},
     "responses": [{"method": "GET", "path": "search/Computer", "status": 400,
                    "body": ["ERROR_GLPI_SEARCH", "bad searchtype"]}]},
    {"id": "commondbtm-list-search-options", "call": "Computer.list_search_options", "args": [1],
     "known_bug": "items_id is passed to glpi_api as raw (TypeError)"},
    {"id": "commondbtm-field-id", "call": "Computer.field_id", "args": ["serial"],
     "known_bug": "calls list_search_options instead of field_id (TypeError)"},
    {"id": "commondbtm-field-uid", "call": "Computer.field_uid", "args": [5],
     "known_bug": "calls list_search_options instead of field_uid (TypeError)"},
    # --------------------------------------------------------------------- User
    _sub("User", "getAllProfiles", 2),
    _sub("User", "getAllGroups", 2, range="0-9"),
    {"id": "user-getalltickets-requester", "call": "User.getAllTickets", "args": [2]},
    {"id": "user-getalltickets-assigned", "call": "User.getAllTickets", "args": [2, 2]},
    {"id": "user-getalltickets-observer", "call": "User.getAllTickets", "args": [2], "kwargs": {"actor_type": 3,
                                                                                               "range": "0-4"}},
    {"id": "user-getalltickets-unknown-type", "call": "User.getAllTickets", "args": [2, 9]},
    {"id": "user-getbyusername", "call": "User.getByUsername", "args": ["glpi"]},
    {"id": "user-getbyusername-429", "call": "User.getByUsername", "args": ["glpi"],
     "responses": [{"method": "GET", "path": "search/User", "status": 429, "body": "Too Many Requests"}],
     "known_bug": "model searches bypass ApiCommunication.call: glpi_api.GLPIError leaks"},
    {"id": "user-getbyemail", "call": "User.getByEmail", "args": ["glpi@example.test"]},
    # -------------------------------------------------------------------- Group
    {"id": "group-getallusers", "call": "Group.getAllUsers", "args": [5]},
    {"id": "group-adduser", "call": "Group.addUser", "args": [5, 7]},
    {"id": "group-deleteuser", "call": "Group.deleteUser", "args": [5, 7],
     "known_bug": "the link is sent wrapped in a list (input [[{'id': 31}]]) and bypasses ApiCommunication.call",
     "responses": [{"method": "GET", "path": "Group/5/Group_User", "status": 200,
                    "body": [{"id": 31, "groups_id": 5, "users_id": 7}, {"id": 32, "groups_id": 5, "users_id": 8}]}]},
    {"id": "group-deleteuser-not-member", "call": "Group.deleteUser", "args": [5, 9],
     "responses": [{"method": "GET", "path": "Group/5/Group_User", "status": 200,
                    "body": [{"id": 31, "groups_id": 5, "users_id": 7}]}]},
    {"id": "group-deleteuser-empty-group", "call": "Group.deleteUser", "args": [5, 7],
     "responses": [{"method": "GET", "path": "Group/5/Group_User", "status": 200, "body": []}]},
    {"id": "group-getalltickets-assigned", "call": "Group.getAllTickets", "args": [5]},
    {"id": "group-getalltickets-requester", "call": "Group.getAllTickets", "args": [5, 1]},
    {"id": "group-getalltickets-observer", "call": "Group.getAllTickets", "args": [5, 3]},
    {"id": "group-getbyname", "call": "Group.getByName", "args": ["Support"]},
    # ----------------------------------------------------------------- Computer
    {"id": "computer-getbyname", "call": "Computer.getByName", "args": ["pc-01"]},
    {"id": "computer-getbyserial", "call": "Computer.getBySerial", "args": ["SN1"]},
    {"id": "computer-getbypatrimonio", "call": "Computer.getByPatrimonio", "args": ["INV-1"]},
    _sub("Computer", "getOperatingSystem", 3),
    _sub("Computer", "getSoftwares", 3),
    _sub("Computer", "getNetworkPorts", 3),
    _sub("Computer", "getProcessors", 3),
    _sub("Computer", "getMemories", 3),
    _sub("Computer", "getDisks", 3),
    _sub("Computer", "getHardDrives", 3),
    _sub("Computer", "getVirtualMachines", 3),
    {"id": "computer-gettickets", "call": "Computer.getTickets", "args": [3]},
    _sub("Computer", "getInfocom", 3),
    _sub("Computer", "getLogs", 3, range="0-4"),
    # ----------------------------------------------------------------- Location
    {"id": "location-getbyname", "call": "Location.getByName", "args": ["Building"]},
    {"id": "location-getbycode", "call": "Location.getByCode", "args": ["A01"]},
    {"id": "location-getbycompletename", "call": "Location.getByCompleteName", "args": ["HQ > Building A"]},
    {"id": "location-getchildren", "call": "Location.getChildren", "args": [7]},
    {"id": "location-getroots", "call": "Location.getRoots"},
    {"id": "location-getcomputers", "call": "Location.getComputers", "args": [7]},
    {"id": "location-getnetworkequipments", "call": "Location.getNetworkEquipments", "args": [7]},
    {"id": "location-gettickets", "call": "Location.getTickets", "args": [7]},
    {"id": "location-getusers", "call": "Location.getUsers", "args": [7]},
    _sub("Location", "getLogs", 7),
    {"id": "location-addfromlist", "call": "Location.addFromList",
     "args": [[{"name": "Room 1", "code": "R1"}, {"name": "Room 2", "code": "R2"}]],
     "kwargs": {"locations_id": 7, "entities_id": 1}},
    {"id": "location-addfromlist-mapper", "call": "Location.addFromList",
     "args": [[{"label": "room 1", "ref": "R1"}]], "kwargs": {"mapper": "@mapper:upper"}},
    {"id": "location-updatefromlist-empty-server", "call": "Location.updateFromList",
     "args": [[{"name": "Room 1", "code": "R1"}]],
     "responses": [{"method": "GET", "path": "Location", "status": 200, "body": []}],
     "known_bug": "warning written with print()"},
    {"id": "location-updatefromlist-no-mapper", "call": "Location.updateFromList",
     "args": [[{"name": "Building A", "code": "A01", "comment": "same"}]], "kwargs": {"mapper": None},
     "responses": [{"method": "GET", "path": "Location", "status": 200, "body": _EXISTING_LOCATIONS}]},
    {"id": "location-updatefromlist-match-key", "call": "Location.updateFromList",
     "args": [[{"label": "renamed", "ref": "A01"}]], "kwargs": {"mapper": "@mapper:upper"},
     "responses": [{"method": "GET", "path": "Location", "status": 200, "body": _EXISTING_LOCATIONS}]},
    {"id": "location-updatefromlist-match-name", "call": "Location.updateFromList",
     "args": [[{"name": "Building B", "code": "B01"}]],
     "responses": [{"method": "GET", "path": "Location", "status": 200, "body": _EXISTING_LOCATIONS}]},
    {"id": "location-updatefromlist-new", "call": "Location.updateFromList",
     "args": [[{"name": "Building C", "code": "C01"}]], "kwargs": {"locations_id": 7, "entities_id": 1},
     "responses": [{"method": "GET", "path": "Location", "status": 200, "body": _EXISTING_LOCATIONS}]},
    {"id": "location-updatefromlist-custom-key", "call": "Location.updateFromList",
     "args": [[{"name": "Building A2", "comment": "x", "id_ext": "77"}]], "kwargs": {"key_field": "id_ext"},
     "responses": [{"method": "GET", "path": "Location", "status": 200,
                    "body": [{"id": 9, "name": "Building A", "id_ext": 77}]}]},
    {"id": "location-updatefromlist-duplicate", "call": "Location.updateFromList",
     "args": [[{"name": "Hidden", "code": "H01"}]],
     "responses": [{"method": "GET", "path": "Location", "status": 200, "body": _EXISTING_LOCATIONS},
                   {"method": "POST", "path": "Location", "status": 400,
                    "body": ["ERROR_GLPI_ADD", "Duplicate entry 'Hidden' for key 'unicity'"]}],
     "known_bug": "Duplicate entry swallowed as {'skipped': True} with a print() warning"},
    {"id": "location-updatefromlist-add-error", "call": "Location.updateFromList",
     "args": [[{"name": "Broken", "code": "X01"}]],
     "responses": [{"method": "GET", "path": "Location", "status": 200, "body": _EXISTING_LOCATIONS},
                   {"method": "POST", "path": "Location", "status": 400, "body": _ERR_400}]},
    {"id": "location-updatefromlist-non-list", "call": "Location.updateFromList",
     "args": [[{"name": "Room 9", "code": "R9"}]],
     "responses": [{"method": "GET", "path": "Location", "status": 200, "body": {"unexpected": True}}]},
    # ------------------------------------------------------------------- Ticket
    {"id": "ticket-addfollowup", "call": "Ticket.addFollowUp", "args": [10, {"content": "hello", "is_private": 0}],
     "known_bug": "the input dict is mutated (items_id/itemtype added)"},
    {"id": "ticket-updatefollowup", "call": "Ticket.updateFollowUp", "args": [40, {"content": "edited"}]},
    {"id": "ticket-deletefollowup", "call": "Ticket.deleteFollowUp", "args": [40]},
    {"id": "ticket-getfollowups", "call": "Ticket.getFollowUps", "args": [10]},
    {"id": "ticket-searchfollowups", "call": "Ticket.searchFollowUps",
     "kwargs": {"criteria": [{"field": 1, "searchtype": "contains", "value": "x"}]},
     "known_bug": "kwargs passed positionally to search (TypeError)"},
    {"id": "ticket-addsolution", "call": "Ticket.addSolution", "args": [10, {"content": "fixed"}]},
    {"id": "ticket-updatesolution", "call": "Ticket.updateSolution", "args": [50, {"content": "fixed again"}]},
    {"id": "ticket-deletesolution", "call": "Ticket.deleteSolution", "args": [50]},
    {"id": "ticket-getsolution", "call": "Ticket.getSolution", "args": [10]},
    {"id": "ticket-approvalsolution", "call": "Ticket.ApprovalSolution", "args": [50],
     "known_bug": "sends ITILSolution.add(solution_id) instead of approving the solution"},
    {"id": "ticket-addvalidation", "call": "Ticket.addValidation", "args": [10, {"users_id_validate": 2}]},
    {"id": "ticket-updatevalidation", "call": "Ticket.updateValidation", "args": [60, {"status": 2}]},
    {"id": "ticket-deletevalidation", "call": "Ticket.deleteValidation", "args": [60]},
    {"id": "ticket-getvalidations", "call": "Ticket.getValidations", "args": [10]},
    {"id": "ticket-addtask", "call": "Ticket.addTask", "args": [10, {"content": "do it", "state": 1}]},
    {"id": "ticket-updatetask", "call": "Ticket.updateTask", "args": [70, {"state": 2}]},
    {"id": "ticket-deletetask", "call": "Ticket.deleteTask", "args": [70]},
    {"id": "ticket-gettasks", "call": "Ticket.getTasks", "args": [10]},
    {"id": "ticket-additem", "call": "Ticket.addItem", "args": [10, {"itemtype": "Computer", "items_id": 3}],
     "known_bug": "items_id/itemtype of the asset are overwritten with the ticket id and 'Ticket'"},
    {"id": "ticket-deleteitem", "call": "Ticket.deleteItem", "args": [80]},
    {"id": "ticket-getitems", "call": "Ticket.getItems", "args": [10]},
    {"id": "ticket-addactor", "call": "Ticket.addActor", "args": [10, {"type": 2, "users_id": 2}],
     "known_bug": "sends items_id/itemtype instead of tickets_id for Ticket_User"},
    {"id": "ticket-deleteactor", "call": "Ticket.deleteActor", "args": [90]},
    {"id": "ticket-getactors", "call": "Ticket.getActors", "args": [10]},
    {"id": "ticket-addlinkedticket", "call": "Ticket.addLinkedTicket", "args": [10, {"tickets_id_2": 11, "link": 1}],
     "known_bug": "sends items_id/itemtype instead of tickets_id_1 for Ticket_Ticket"},
    {"id": "ticket-deletelinkedticket", "call": "Ticket.deleteLinkedTicket", "args": [95]},
    {"id": "ticket-getlinkedtickets", "call": "Ticket.getLinkedTickets", "args": [10]},
    # ---------------------------------------------------------- TicketDashboard
    {"id": "dashboard-metrics", "call": "TicketDashboard._metrics", "args": ["2026-01-01", "2026-01-31"]},
    {"id": "dashboard-metrics-category", "call": "TicketDashboard._metrics", "args": ["2026-01-01", "2026-01-31", 3]},
    {"id": "dashboard-collect-data", "call": "TicketDashboard.collect_data", "args": ["2026-01-01", "2026-01-31"]},
    {"id": "dashboard-diagnose", "call": "TicketDashboard.diagnose", "args": ["2026-01-01", "2026-01-31", 3],
     "known_bug": "debug output written with print()"},
    {"id": "dashboard-generate-without-plotly", "call": "TicketDashboard.generate",
     "args": ["2026-01-01", "2026-01-31"], "kwargs": {"data": {"categorias": {}}}},
    # ------------------------------------------------- new in the normalized contract (no point A)
    {"id": "commondbtm-add-sub-item", "since": "v2", "call": "Computer.add_sub_item",
     "args": [3, "Item_OperatingSystem", {"operatingsystems_id": 1}]},
    {"id": "commondbtm-update-sub-item", "since": "v2", "call": "Computer.update_sub_item",
     "args": [3, "Item_OperatingSystem", 11, {"operatingsystems_id": 2}]},
    {"id": "commondbtm-delete-sub-item", "since": "v2", "call": "Computer.delete_sub_item",
     "args": [3, "Item_OperatingSystem", 11]},
    {"id": "location-updatefromlist-duplicate-list-answer", "since": "v2", "call": "Location.updateFromList",
     "args": [[{"name": "Hidden", "code": "H01"}]],
     "responses": [{"method": "GET", "path": "Location", "status": 200, "body": _EXISTING_LOCATIONS},
                   {"method": "POST", "path": "Location", "status": 400,
                    "body": ["ERROR_GLPI_ADD",
                             [{"id": False, "message": "Duplicate entry 'Hidden' for key 'unicity'"}]]}],
     "known_bug": "Duplicate entry swallowed as {'skipped': True} with a print() warning"},
    {"id": "commondbtm-add-many-empty", "since": "v2", "call": "Location.add_many", "args": [[]]},
    {"id": "commondbtm-update-many-empty", "since": "v2", "call": "Location.update_many", "args": [[]]},
    {"id": "commondbtm-delete-many-empty", "since": "v2", "call": "Location.delete_many", "args": [[]]},
    {"id": "dashboard-collect-data-categories", "call": "TicketDashboard.collect_data",
     "args": ["2026-01-01", "2026-01-31", {"Infrastructure": 3, "Systems": 5}]},
]


# ---------------------------------------------------------------------------
# Normalized contract (phase 02): overrides applied on top of each scenario.
#
# Keys: call/args/kwargs/steps (new names and signatures, D7), known_bug (None when
# fixed), fixed (what was corrected), requests_change (decision that changed the
# requests sent; without it the requests must stay identical to point A).
# ---------------------------------------------------------------------------
_D19 = "D19: user token sent in the Authorization header (known bug fixed)"
_D20 = "D20: search options, field_id and field_uid query listSearchOptions (known bug fixed)"
_D21 = "D21: Group.deleteUser sends input [{'id': N}] through CommonDBTM (known bug fixed)"
_D23 = "D23: getLoggedUser reads User/<glpiID> of the session (known bug fixed)"
_D29 = "D29: a failed single delete reads the item back to tell missing (NotFoundError) from refused"
_D22 = "D22: CommonDBTM.add takes one dict; a non-dict payload fails before any request"

V2: dict[str, dict[str, Any]] = {
    "session-set-connection-parameters": {"known_bug": None,
                                          "fixed": "user token stored under 'usertoken'"},
    "session-init-user-token": {"known_bug": None, "requests_change": _D19, "fixed": _D19},
    "session-init-insecure-default": {"known_bug": None, "fixed": "TLS verified by default"},
    "session-set-profile-entity-404": {"known_bug": None, "fixed": "mapped to NotFoundError"},
    "session-get-logged-user": {"known_bug": None, "requests_change": _D23, "fixed": _D23},
    "session-call-get-config": {"args": ["@connector:get_config"]},
    "session-call-429": {"args": ["@connector:get_config"]},
    "commondbtm-add-many": {"call": "Location.add_many", "args": [[{"name": "loc-a"}, {"name": "loc-b"}]]},
    "commondbtm-add-207": {"call": "Location.add_many", "args": [[{"name": "loc-a"}, {"name": "loc-a"}]]},
    "commondbtm-update-one": {"args": [7, {"name": "loc-x"}]},
    "commondbtm-update-many": {"call": "Location.update_many",
                               "args": [[{"id": 7, "name": "loc-x"}, {"id": 8, "name": "loc-y"}]]},
    "commondbtm-update-207": {"call": "Location.update_many",
                              "args": [[{"id": 7, "name": "loc-x"}, {"id": 999, "name": "loc-y"}]]},
    "commondbtm-delete-one": {"args": [7]},
    "commondbtm-delete-many": {"call": "Location.delete_many", "args": [[7, 8]]},
    "commondbtm-delete-force-purge": {"args": [7]},
    "commondbtm-delete-error-glpi-delete": {
        "args": [999], "known_bug": None, "requests_change": _D29, "fixed": _D29,
        "responses": [{"method": "DELETE", "path": "Location", "status": 400,
                       "body": ["ERROR_GLPI_DELETE", [{"999": False, "message": "Item not found"}]]},
                      {"method": "GET", "path": "Location/999", "status": 404,
                       "body": ["ERROR_ITEM_NOT_FOUND", "Item not found"]}]},
    "commondbtm-delete-400": {"args": [7]},
    "commondbtm-get-all-items": {"call": "Location.get_all"},
    "commondbtm-get-all-items-range-sort": {"call": "Location.get_all"},
    "commondbtm-get-all-items-206": {"call": "Location.get_all"},
    "commondbtm-get-all-items-searchtext": {"call": "Location.get_all"},
    "commondbtm-list-search-options": {"call": "Computer.search_options", "args": [], "known_bug": None,
                                       "requests_change": _D20, "fixed": _D20},
    "commondbtm-field-id": {"known_bug": None, "requests_change": _D20, "fixed": _D20},
    "commondbtm-field-uid": {"known_bug": None, "requests_change": _D20, "fixed": _D20},
    "user-getbyusername-429": {"known_bug": None, "fixed": "mapped to RateLimitError"},
    "group-deleteuser": {"known_bug": None, "requests_change": _D21, "fixed": _D21},
    "ticket-approvalsolution": {"requests_change": _D22},
}


# Public method renames of phase 04.1 (snake_case, D32): old ``Class.method`` -> new name
CALL_RENAMES: dict[str, str] = {
    "User.getAllProfiles": "User.get_profiles",
    "User.getAllGroups": "User.get_groups",
    "User.getAllTickets": "User.get_tickets",
    "User.getByUsername": "User.get_by_username",
    "User.getByEmail": "User.get_by_email",
    "Group.getAllUsers": "Group.get_users",
    "Group.addUser": "Group.add_user",
    "Group.deleteUser": "Group.delete_user",
    "Group.getAllTickets": "Group.get_tickets",
    "Group.getByName": "Group.get_by_name",
    "Computer.getByName": "Computer.get_by_name",
    "Computer.getBySerial": "Computer.get_by_serial",
    "Computer.getByPatrimonio": "Computer.get_by_inventory_number",
    "Computer.getOperatingSystem": "Computer.get_operating_system",
    "Computer.getSoftwares": "Computer.get_softwares",
    "Computer.getNetworkPorts": "Computer.get_network_ports",
    "Computer.getProcessors": "Computer.get_processors",
    "Computer.getMemories": "Computer.get_memories",
    "Computer.getDisks": "Computer.get_disks",
    "Computer.getHardDrives": "Computer.get_hard_drives",
    "Computer.getVirtualMachines": "Computer.get_virtual_machines",
    "Computer.getTickets": "Computer.get_tickets",
    "Computer.getInfocom": "Computer.get_infocom",
    "Computer.getLogs": "Computer.get_logs",
    "Location.getByName": "Location.get_by_name",
    "Location.getByCode": "Location.get_by_code",
    "Location.getByCompleteName": "Location.get_by_complete_name",
    "Location.getChildren": "Location.get_children",
    "Location.getRoots": "Location.get_roots",
    "Location.getComputers": "Location.get_computers",
    "Location.getNetworkEquipments": "Location.get_network_equipments",
    "Location.getTickets": "Location.get_tickets",
    "Location.getUsers": "Location.get_users",
    "Location.addFromList": "Location.add_from_list",
    "Location.updateFromList": "Location.update_from_list",
    "Location.getLogs": "Location.get_logs",
    "Ticket.addFollowUp": "Ticket.add_followup",
    "Ticket.updateFollowUp": "Ticket.update_followup",
    "Ticket.deleteFollowUp": "Ticket.delete_followup",
    "Ticket.getFollowUps": "Ticket.get_followups",
    "Ticket.searchFollowUps": "Ticket.search_followups",
    "Ticket.addSolution": "Ticket.add_solution",
    "Ticket.updateSolution": "Ticket.update_solution",
    "Ticket.deleteSolution": "Ticket.delete_solution",
    "Ticket.getSolution": "Ticket.get_solutions",
    "Ticket.ApprovalSolution": "Ticket.approve_solution",
    "Ticket.addValidation": "Ticket.add_validation",
    "Ticket.updateValidation": "Ticket.update_validation",
    "Ticket.deleteValidation": "Ticket.delete_validation",
    "Ticket.getValidations": "Ticket.get_validations",
    "Ticket.addTask": "Ticket.add_task",
    "Ticket.updateTask": "Ticket.update_task",
    "Ticket.deleteTask": "Ticket.delete_task",
    "Ticket.getTasks": "Ticket.get_tasks",
    "Ticket.addItem": "Ticket.add_item",
    "Ticket.deleteItem": "Ticket.delete_item",
    "Ticket.getItems": "Ticket.get_items",
    "Ticket.addActor": "Ticket.add_actor",
    "Ticket.deleteActor": "Ticket.delete_actor",
    "Ticket.getActors": "Ticket.get_actors",
    "Ticket.addLinkedTicket": "Ticket.add_linked_ticket",
    "Ticket.deleteLinkedTicket": "Ticket.delete_linked_ticket",
    "Ticket.getLinkedTickets": "Ticket.get_linked_tickets",
}


def _rename_calls(scenario: dict[str, Any]) -> dict[str, Any]:
    """Apply ``CALL_RENAMES`` to a scenario call and to its steps.

    Args:
        scenario: Scenario dict.

    Returns:
        A copy with the new method names.
    """
    out = dict(scenario)
    if "call" in out:
        out["call"] = CALL_RENAMES.get(out["call"], out["call"])
    if "steps" in out:
        out["steps"] = [{**step, "call": CALL_RENAMES.get(step["call"], step["call"])} for step in out["steps"]]
    return out


def normalized(scenario: dict[str, Any]) -> dict[str, Any]:
    """Return a scenario with its normalized-contract overrides applied.

    Args:
        scenario: Scenario dict from ``SCENARIOS``.

    Returns:
        A new dict; ``known_bug`` is dropped when the override sets it to ``None``.
    """
    merged = _rename_calls({**scenario, **V2.get(scenario["id"], {})})
    if merged.get("known_bug") is None:
        merged.pop("known_bug", None)
    return merged
