import logging
from dataclasses import dataclass, field
from typing import List, NamedTuple

from toggl_tally import TogglAPI

logger = logging.getLogger(__name__)


TOGGL_ENTITIES = ["project", "client", "workspace"]
TogglEntity = NamedTuple("TogglEntity", [("id", int), ("name", str)])


@dataclass
class TogglEntities:
    entities: List[TogglEntity]
    entity_ids: List[int] = field(init=False)

    def __post_init__(self):
        self.entity_ids = [entity.id for entity in self.entities]


class TogglFilter(object):
    def __init__(
        self,
        api: TogglAPI,
        projects: List[str] = [],
        clients: List[str] = [],
        workspaces: List[str] = [],
    ):
        self.api = api
        self.projects: TogglEntities = self._get_user_projects(projects)
        self.clients: TogglEntities = self._get_user_clients(clients)
        self.workspaces: TogglEntities = self._get_user_workspaces(workspaces)

    def filter_time_entries(self, response: List[dict]):
        # can only filter time entries directly by project and workspace ID
        # must filter by client by excluding non-client projects
        for time_entry in response:
            pass

    @staticmethod
    def get_toggl_entities(
        response: List[dict],
        toggl_entity: str,
        entity_names: List[str],
    ):
        if toggl_entity not in TOGGL_ENTITIES:
            raise ValueError(f"toggl_entity_name should be one of {TOGGL_ENTITIES}")
        names_to_ids = {
            entity_dict["name"]: entity_dict["id"] for entity_dict in response
        }
        entities = []
        for entity_name in entity_names:
            try:
                entity_id = names_to_ids[entity_name]
            except KeyError:
                raise ValueError(
                    f"{toggl_entity.title()} name {entity_name} not found in"
                    f" user {TOGGL_ENTITIES}s"
                )
            entities.append(TogglEntity(id=entity_id, name=entity_name))
        return TogglEntities(entities)

    def _get_user_projects(self, project_names: List[str]):
        if not project_names:
            return project_names
        user_projects = self.api.get_user_projects()
        return self.get_toggl_entities(
            response=user_projects,
            toggle_entity="project",
            entity_names=project_names,
        )

    def _get_user_clients(self, client_names: List[str]):
        if not client_names:
            return client_names
        user_clients = self.api.get_user_clients()
        return self.get_toggl_entities(
            response=user_clients,
            toggle_entity="client",
            entity_names=client_names,
        )

    def _get_user_workspaces(self, workspace_names: List[str]):
        if not workspace_names:
            return workspace_names
        user_workspaces = self.api.get_user_workspaces()
        return self.get_toggl_entities(
            response=user_workspaces,
            toggle_entity="workspace",
            entity_names=workspace_names,
        )
