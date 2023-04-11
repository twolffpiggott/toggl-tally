import logging
from dataclasses import dataclass, field
from typing import List, NamedTuple, Set

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
        self.filtered_client_projects = self._filter_client_projects()

    def filter_time_entries(
        self, response: List[dict], exclude_running_entries: bool = True
    ) -> List[dict]:
        """
        Time entries always have a workspace
        Time entries may have a project
        Time entries only have clients by way of projects
        Projects can have no client

        Caller provides incompatible workspaces and clients -> empty result
        """
        workspace_ids_set = self._get_workspace_ids_set()
        project_ids_intersection = self._get_project_ids_intersection()

        return [
            time_entry
            for time_entry in response
            if self._is_valid_time_entry(
                time_entry,
                exclude_running_entries,
                workspace_ids_set,
                project_ids_intersection,
            )
        ]

    def _get_workspace_ids_set(self) -> Set[int]:
        if self.filtered_workspaces:
            return set(self.filtered_workspaces.entity_ids)
        return set()

    def _get_project_ids_intersection(self) -> Set[int]:
        if not self.filtered_projects and not self.filtered_clients:
            return set()

        project_id_sets = []
        if self.filtered_projects:
            project_id_sets.append(set(self.filtered_projects.entity_ids))
        if self.filtered_clients:
            project_id_sets.append(set(self.filtered_client_projects.entity_ids))

        project_ids_intersection = project_id_sets[0]
        for project_id_set in project_id_sets[1:]:
            project_ids_intersection = project_ids_intersection & project_id_set

        return project_ids_intersection

    def _is_valid_time_entry(
        self,
        time_entry: dict,
        exclude_running_entries: bool,
        workspace_ids_set: Set[int],
        project_ids_intersection: Set[int],
    ) -> bool:
        if exclude_running_entries and self._is_running_time_entry(time_entry):
            return False
        if workspace_ids_set and time_entry["workspace_id"] not in workspace_ids_set:
            return False
        if (
            project_ids_intersection
            and time_entry["project_id"] not in project_ids_intersection
        ):
            return False
        return True

    def _is_running_time_entry(self, time_entry: dict) -> bool:
        # Running entries have duration = -1 * (Unix start time)
        # https://developers.track.toggl.com/docs/api/time_entries
        return time_entry["duration"] < 0

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
                    f" user {toggl_entity}s"
                )
            entities.append(
                TogglEntity(id=entity_id, name=entity_name, type=toggl_entity)
            )
        return TogglEntities(entities)

    def _filter_client_projects(
        self,
    ) -> TogglEntities:
        """
        Time entries are only associated with clients by way of projects.
        """
        client_projects_entities = []
        for project_dict in self.user_projects:
            if project_dict["client_id"] in self.filtered_clients.entity_ids:
                client_projects_entities.append(
                    TogglEntity(
                        id=project_dict["id"], name=project_dict["name"], type="project"
                    )
                )
        return TogglEntities(client_projects_entities)

    def _filter_projects(self, project_names: List[str]) -> TogglEntities:
        return self.get_toggl_entities(
            response=self.user_projects,
            toggl_entity="project",
            entity_names=project_names,
        )

    def _filter_clients(self, client_names: List[str]) -> TogglEntities:
        return self.get_toggl_entities(
            response=self.user_clients,
            toggl_entity="client",
            entity_names=client_names,
        )

    def _filter_workspaces(self, workspace_names: List[str]) -> TogglEntities:
        return self.get_toggl_entities(
            response=self.user_workspaces,
            toggl_entity="workspace",
            entity_names=workspace_names,
        )
