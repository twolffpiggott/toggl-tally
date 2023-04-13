import re
from unittest.mock import patch

import pytest

from toggl_tally.filter import TogglEntities, TogglEntity, TogglFilter


@pytest.mark.parametrize(
    "toggl_filter_object,expected_filtered_projects,expected_filtered_clients"
    ",expected_filtered_workspaces",
    [
        pytest.param(
            dict(
                user_projects="user_projects",
                user_clients="user_clients",
                user_workspaces="user_workspaces",
                project_names=["Doohickey design"],
                client_names=["Supercorp"],
                workspace_names=["John Doe's workspace"],
            ),
            TogglEntities(
                entities=[
                    TogglEntity(id=1000, name="Doohickey design", type="project"),
                ]
            ),
            TogglEntities(
                entities=[
                    TogglEntity(id=55, name="Supercorp", type="client"),
                ]
            ),
            TogglEntities(
                entities=[
                    TogglEntity(id=10, name="John Doe's workspace", type="workspace"),
                ]
            ),
            id="get_toggl_entities_base",
        ),
        pytest.param(
            dict(
                user_projects="user_projects",
                user_clients="user_clients",
                user_workspaces="user_workspaces",
                project_names=["Doohickey design", "Project X"],
                client_names=[],
                workspace_names=[],
            ),
            TogglEntities(
                entities=[
                    TogglEntity(id=1000, name="Doohickey design", type="project"),
                    TogglEntity(id=1001, name="Project X", type="project"),
                ]
            ),
            TogglEntities(entities=[]),
            TogglEntities(entities=[]),
            id="get_toggl_entities_empty",
        ),
    ],
    indirect=["toggl_filter_object"],
)
def test_get_toggl_entities(
    toggl_filter_object,
    expected_filtered_projects,
    expected_filtered_clients,
    expected_filtered_workspaces,
):
    assert toggl_filter_object.filtered_projects == expected_filtered_projects
    assert toggl_filter_object.filtered_clients == expected_filtered_clients
    assert toggl_filter_object.filtered_workspaces == expected_filtered_workspaces


def test_get_toggl_entities_fails_for_missing_name(
    user_projects,
    user_clients,
    user_workspaces,
):
    with patch("toggl_tally.TogglAPI") as MockTogglAPI:
        instance = MockTogglAPI.return_value
        instance.get_user_projects.return_value = user_projects
        instance.get_user_clients.return_value = user_clients
        instance.get_user_workspaces.return_value = user_workspaces
        exception_match_str = re.escape(
            "Client name Brawn bazaar not found in user clients"
        )
        with pytest.raises(ValueError, match=exception_match_str):
            TogglFilter(
                api=instance,
                projects=[],
                clients=["Brawn bazaar"],
                workspaces=[],
            )


@pytest.mark.parametrize(
    "toggl_filter_object,expected_filtered_client_projects",
    [
        pytest.param(
            dict(
                user_projects="user_projects",
                user_clients="user_clients",
                user_workspaces="user_workspaces",
                project_names=[],
                client_names=["Supercorp", "Megacorp"],
                workspace_names=[],
            ),
            TogglEntities(
                entities=[
                    TogglEntity(id=1000, name="Doohickey design", type="project"),
                    TogglEntity(id=1002, name="Foo implementation", type="project"),
                    TogglEntity(id=1003, name="Bar implementation", type="project"),
                    TogglEntity(id=1005, name="Baz refactoring", type="project"),
                ]
            ),
            id="filter_client_projects",
        ),
        pytest.param(
            dict(
                user_projects="user_projects",
                user_clients="user_clients",
                user_workspaces="user_workspaces",
                project_names=[],
                client_names=["Another client"],
                workspace_names=[],
            ),
            TogglEntities(entities=[]),
            id="filter_client_projects_empty",
        ),
    ],
    indirect=["toggl_filter_object"],
)
def test_filter_client_projects(
    toggl_filter_object,
    expected_filtered_client_projects,
):
    assert (
        toggl_filter_object.filtered_client_projects
        == expected_filtered_client_projects
    )


@pytest.mark.parametrize(
    "toggl_filter_object,expected_filtered_time_entries_indices",
    [
        pytest.param(
            dict(
                user_projects="user_projects",
                user_clients="user_clients",
                user_workspaces="user_workspaces",
                project_names=[],
                client_names=["Supercorp"],
                workspace_names=[],
            ),
            [0, 1, 2, 6, 7],
            id="filter_time_entries_by_client",
        ),
        pytest.param(
            dict(
                user_projects="user_projects",
                user_clients="user_clients",
                user_workspaces="user_workspaces",
                project_names=[],
                client_names=[],
                workspace_names=["Alternate workspace"],
            ),
            [4],
            id="filter_time_entries_by_workspace",
        ),
        pytest.param(
            dict(
                user_projects="user_projects",
                user_clients="user_clients",
                user_workspaces="user_workspaces",
                project_names=["Course work"],
                client_names=[],
                workspace_names=[],
            ),
            [3, 5],
            id="filter_time_entries_by_project",
        ),
        pytest.param(
            dict(
                user_projects="user_projects",
                user_clients="user_clients",
                user_workspaces="user_workspaces",
                project_names=["Doohickey design"],
                client_names=["Hypermart"],
                workspace_names=[],
            ),
            [0, 1, 2, 4],
            id="filter_time_entries_by_project_and_client",
        ),
        pytest.param(
            dict(
                user_projects="user_projects",
                user_clients="user_clients",
                user_workspaces="user_workspaces",
                project_names=["Doohickey design"],
                client_names=["Supercorp"],
                workspace_names=["Alternate workspace"],
            ),
            [0, 1, 2, 4, 6, 7],
            id="filter_time_entries_by_project_client_and_workspace",
        ),
        pytest.param(
            dict(
                user_projects="user_projects",
                user_clients="user_clients",
                user_workspaces="user_workspaces",
                project_names=[
                    "Doohickey design",
                    "Foo implementation",
                    "Baz refactoring",
                ],
                client_names=[],
                workspace_names=[],
            ),
            [0, 1, 2, 6, 9],
            id="filter_time_entries_by_project_multiple",
        ),
        pytest.param(
            dict(
                user_projects="user_projects",
                user_clients="user_clients",
                user_workspaces="user_workspaces",
                project_names=[],
                client_names=["Megacorp", "Hypermart"],
                workspace_names=[],
            ),
            [4, 9],
            id="filter_time_entries_by_client_multiple",
        ),
    ],
    indirect=["toggl_filter_object"],
)
def test_filter_time_entries(
    toggl_filter_object, expected_filtered_time_entries_indices, time_entries
):
    expected_filtered_time_entries = [
        time_entries[index] for index in expected_filtered_time_entries_indices
    ]
    filtered_time_entries = toggl_filter_object.filter_time_entries(time_entries)
    assert filtered_time_entries == expected_filtered_time_entries
