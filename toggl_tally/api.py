import os
from datetime import datetime, timezone
from typing import Dict, List, Union

import requests
from requests.exceptions import HTTPError


class TogglAPI(object):
    def __init__(
        self,
        base_url: str = "https://api.track.toggl.com/api/v9",
        headers: Dict[str, str] = {"content-type": "application/json"},
    ):
        self.base_url = base_url
        self.headers = headers
        self.session = requests.Session()
        self.auth()

    def auth(self):
        try:
            api_token = os.environ["TOGGL_API_TOKEN"]
        except KeyError as exception:
            raise KeyError(
                "Please ensure that the 'TOGGL_API_TOKEN' environment variable is set"
            ) from exception
        self.session.auth = (api_token, "api_token")

    def get_time_entries(self):
        current_timestamp = self._get_current_timestamp()
        params = dict(before=current_timestamp)
        return self._call_toggl_api(f"{self.base_url}/me/time_entries", params=params)

    def get_user_workspaces(self) -> List[dict]:
        return self._call_toggl_api(f"{self.base_url}/me/workspaces")

    def get_user_clients(self) -> List[dict]:
        return self._call_toggl_api(f"{self.base_url}/me/clients")

    def get_user_projects(self) -> List[dict]:
        return self._call_toggl_api(f"{self.base_url}/me/projects")

    def _call_toggl_api(
        self, url: str, params: Union[dict, None] = None
    ) -> Union[dict, None]:
        kwargs = dict(headers=self.headers)
        if params is not None:
            kwargs["params"] = params
        response = self.session.get(url, **kwargs)
        if response.ok:
            return response.json()
        # give more info in the case of a bad request
        elif response.status_code == 400:
            error_msg = (
                f"{response.status_code} Client Error: {response.text} for url: {url}"
            )
            raise HTTPError(error_msg)
        else:
            response.raise_for_status()

    @staticmethod
    def _get_current_timestamp() -> str:
        """
        RFC3339 format https://developers.track.toggl.com/docs/api/time_entries
        """
        local_time = datetime.now(timezone.utc).astimezone()
        return local_time.isoformat()
