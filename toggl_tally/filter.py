import logging
from dataclasses import dataclass, field
from typing import List, NamedTuple, Tuple

from toggl_tally import TogglAPI

logger = logging.getLogger(__name__)


TOGGL_ENTITIES = ["project", "client", "workspace"]
TogglEntity = NamedTuple("TogglEntity", [("id", int), ("name", str), ("type", str)])


@dataclass
class TogglEntities:
    entities: List[TogglEntity]
    entity_ids: List[int] = field(init=False)

    def __post_init__(self):
        self.entity_ids = [entity.id for entity in self.entities]

    def __bool__(self):
        return bool(self.entities)


class TogglFilter(object):
    def __init__(
        self,
        api: TogglAPI,
        projects: List[str] = [],
        clients: List[str] = [],
        workspaces: List[str] = [],
    ):
        self.api = api
        self.user_projects: List[dict] = self.api.get_user_projects()
        self.user_clients: List[dict] = self.api.get_user_clients()
        self.user_workspaces: List[dict] = self.api.get_user_workspaces()
        self.filtered_projects: TogglEntities = self._filter_projects(projects)
        self.filtered_clients: TogglEntities = self._filter_clients(clients)
        self.filtered_workspaces: TogglEntities = self._filter_workspaces(workspaces)
        (
            self.filtered_client_projects,
            self.filtered_workspace_projects,
        ) = self._filter_client_and_workspace_projects()

    def filter_time_entries(self, response: List[dict]):
        # can only filter time entries directly by project and workspace ID
        # must filter by client by excluding non-client projects
        # complications: caller could provide incompatible workspaces and clients
        # answer: then give them an empty result!
        # easiest path: filter only by projects
        # maintain a set of project IDs
        for time_entry in response:
            pass

    @staticmethod
    def get_toggl_entities(
        response: List[dict],
        toggl_entity: str,
        entity_names: List[str],
    ) -> TogglEntities:
        if toggl_entity not in TOGGL_ENTITIES:
            raise ValueError(f"toggl_entity_name should be one of {TOGGL_ENTITIES}")
        if not entity_names:
            return TogglEntities(entity_names)
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
            entities.append(
                TogglEntity(id=entity_id, name=entity_name, type=entity_name)
            )
        return TogglEntities(entities)

    def _filter_client_and_workspace_projects(
        self,
    ) -> Tuple[TogglEntities, TogglEntities]:
        client_projects_entities = []
        workspace_projects_entities = []
        for project_dict in self.user_projects:
            if project_dict["client_id"] in self.filtered_clients.entity_ids:
                client_projects_entities.append(
                    TogglEntity(
                        id=project_dict["id"], name=project_dict["name"], type="project"
                    )
                )
            if project_dict["workspace_id"] in self.filtered_workspaces.entity_ids:
                workspace_projects_entities.append(
                    TogglEntity(
                        id=project_dict["id"], name=project_dict["name"], type="project"
                    )
                )
        return TogglEntities(client_projects_entities), TogglEntities(
            workspace_projects_entities
        )

    def _filter_projects(self, project_names: List[str]) -> TogglEntities:
        return self.get_toggl_entities(
            response=self.user_projects,
            toggle_entity="project",
            entity_names=project_names,
        )

    def _filter_clients(self, client_names: List[str]) -> TogglEntities:
        return self.get_toggl_entities(
            response=self.user_clients,
            toggle_entity="client",
            entity_names=client_names,
        )

    def _filter_workspaces(self, workspace_names: List[str]) -> TogglEntities:
        return self.get_toggl_entities(
            response=self.user_workspaces,
            toggle_entity="workspace",
            entity_names=workspace_names,
        )
