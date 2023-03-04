import pytest

from toggl_tally.filter import TogglEntities, TogglEntity


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
