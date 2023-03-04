from unittest.mock import PropertyMock, patch

import pytest

from toggl_tally import TogglFilter, TogglTally


@pytest.fixture()
def toggl_tally_object(request):
    kwargs = request.param
    with patch(
        "toggl_tally.TogglTally.now", new_callable=PropertyMock
    ) as mock_toggl_tally_now:
        mock_toggl_tally_now.return_value = kwargs["now"]
        tally_object = TogglTally(
            invoice_day_of_month=kwargs.get("invoice_day_of_month", 1),
            skip_today=kwargs.get("skip_today", False),
            exclude_public_holidays=kwargs.get("exclude_public_holidays", True),
        )
        yield tally_object


@pytest.fixture()
def toggl_filter_object(request):
    kwargs = request.param
    with patch("toggl_tally.TogglAPI") as MockTogglAPI:
        instance = MockTogglAPI.return_value
        instance.get_user_projects.return_value = request.getfixturevalue(
            kwargs["user_projects"]
        )
        instance.get_user_clients.return_value = request.getfixturevalue(
            kwargs["user_clients"]
        )
        instance.get_user_workspaces.return_value = request.getfixturevalue(
            kwargs["user_workspaces"]
        )
        yield TogglFilter(
            api=instance,
            projects=kwargs["project_names"],
            clients=kwargs["client_names"],
            workspaces=kwargs["workspace_names"],
        )


@pytest.fixture()
def user_workspaces():
    return [
        {"name": "John Doe's workspace", "id": 10},
        {"name": "Alternate workspace", "id": 11},
    ]


@pytest.fixture()
def user_clients():
    return [
        {"name": "Supercorp", "id": 55, "wid": 10},
        {"name": "Another client", "id": 20, "wid": 10},
        {"name": "Hypermart", "id": 40, "wid": 11},
    ]


@pytest.fixture()
def user_projects():
    return [
        {"name": "Doohickey design", "id": 1000, "workspace_id": 10, "client_id": 55},
        {"name": "Course work", "id": 1030, "workspace_id": 10, "client_id": None},
        {"name": "Project X", "id": 1001, "workspace_id": 11, "client_id": 40},
    ]


@pytest.fixture()
def time_entries():
    return [
        {
            "id": 1000001,
            "workspace_id": 10,
            "project_id": 1000,
            "duration": 3600,
            "description": "Design part 1",
        },
        {
            "id": 1000002,
            "workspace_id": 10,
            "project_id": 1000,
            "duration": 3600,
            "description": "Design part 2",
        },
        {
            "id": 1000003,
            "workspace_id": 10,
            "project_id": 1000,
            "duration": 3600,
            "description": "Design part 3",
        },
        {
            "id": 1000010,
            "workspace_id": 10,
            "project_id": 1030,
            "duration": 1800,
            "description": "Module 5",
        },
        {
            "id": 1000012,
            "workspace_id": 11,
            "project_id": 1001,
            "duration": 1800,
            "description": "Phase 2 ideation",
        },
    ]
