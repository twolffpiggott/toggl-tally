import logging
from typing import List, NamedTuple

from toggl_tally import TogglAPI

logger = logging.getLogger(__name__)


TogglEntity = NamedTuple("TogglEntity", [("id", int), ("name", str)])


class TogglFilter(object):
    def __init__(
        self,
        api: TogglAPI,
        projects: List[str],
        clients: List[str],
        workspaces: List[str],
    ):
        self.api = api
        self.projects = projects
        self.clients = clients
        self.workspaces: List[TogglEntity] = self._get_user_workspaces(workspaces)

    def _get_user_workspaces(self, workspace_names: List[str]):
        user_workspaces = self.api.get_user_workspaces()
        names_to_ids = {
            workspace_dict["name"]: workspace_dict["id"]
            for workspace_dict in user_workspaces
        }
        workspaces = []
        for workspace_name in workspace_names:
            try:
                workspace_id = names_to_ids[workspace_name]
            except KeyError:
                raise ValueError(
                    f"Workspace name {workspace_name} not found in user workspaces"
                )
            workspaces.append(TogglEntity(id=workspace_id, name=workspace_name))
        return workspaces
