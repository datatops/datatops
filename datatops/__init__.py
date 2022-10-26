import pathlib
from typing import Dict, List, Optional, Union
import json

import requests

from .config import (
    ADMIN_KEY_HEADER,
    USER_KEY_HEADER,
    PROJECT_CREATION_SECRET_HEADER,
)


def _namespaced_url(url: str):
    """
    Make a URL a safe string for a directory name on disk.

    """
    return (
        url.removeprefix("https://")
        .removeprefix("http://")
        .replace("/", "_")
        .replace(":", "_")
    )


class Project:
    """
    A high-level class to manage data in a specific Project.

    """

    @staticmethod
    def from_json(json_path: Union[str, pathlib.Path]):
        """
        Create a Project object from a json file.

        Arguments:
            json_path (str): The path to the json file.

        """
        with open(json_path) as f:
            project = json.load(f)
            return Project(
                project["name"],
                project["admin_key"],
                project["user_key"],
                project["url"],
            )

    def __init__(
        self,
        name: str,
        admin_key: Optional[str] = None,
        user_key: Optional[str] = None,
        url: Optional[str] = None,
    ):
        """
        Create a new Project object.

        If you have the admin key, you can use that to create the Project object.
        Otherwise, you can use the url or json to create the Project object.

        Arguments:
            name (str): The name of the project.
            admin_key (str): The admin key for the project.
            user_key (str): The user key for the project.
            url (str): The url for the project.
            json (str): The path to a json file containing the project details.

        """
        if name.endswith(".json"):
            with open(name) as f:
                project = json.load(f)
                self.name = project["name"]
                self.admin_key = project["admin_key"]
                self.user_key = project["user_key"]
                self.url = project["url"]
            return
        self.name = name
        self.admin_key = admin_key
        self.user_key = user_key
        self.url = url

    def __repr__(self):
        return f"""Project({self.to_json()})"""

    def to_dict(self):
        """
        Return the project details as a json string.

        """
        return {
            "name": self.name,
            **({"admin_key": self.admin_key} if self.admin_key else {}),
            **({"user_key": self.user_key} if self.user_key else {}),
            **({"url": self.url} if self.url else {}),
        }

    def to_json(self):
        """
        Return the project details as a json string.

        """
        return json.dumps(self.to_dict(), indent=4)

    def save_json(self, path: str):
        """
        Save the project details to a json file.

        """
        with open(path, "w") as f:
            f.write(self.to_json())

    def _get(self, url: str, **kwargs) -> Dict:
        """
        Make a GET request to the Datatops API.

        Arguments:
            url (str): The url to make the request to.

        Returns:
            Dict: The response from the Datatops API.

        """
        headers = {}
        if self.admin_key:
            headers[ADMIN_KEY_HEADER] = self.admin_key
        elif self.user_key:
            headers[USER_KEY_HEADER] = self.user_key

        # Merge the headers from the kwargs
        headers.update(kwargs.pop("headers", {}))

        response = requests.get(url, headers=headers, **kwargs)
        return response.json()

    def _post(self, url: str, **kwargs) -> Dict:
        """
        Make a POST request to the Datatops API.

        Arguments:
            url (str): The url to make the request to.

        Returns:
            Dict: The response from the Datatops API.

        """
        headers = {}
        if self.admin_key:
            headers[ADMIN_KEY_HEADER] = self.admin_key
        elif self.user_key:
            headers[USER_KEY_HEADER] = self.user_key

        # Merge the headers from the kwargs
        headers.update(kwargs.pop("headers", {}))

        response = requests.post(url, headers=headers, **kwargs)
        return response.json()

    # Data methods
    def list_data(self, limit: Optional[int] = None) -> List[Dict]:
        """
        List all data for the project.

        Arguments:
            limit (int): The maximum number of records to return.

        Returns:
            List[Dict]: A list of dictionaries containing the data.

        """
        # "/api/v1/projects/<project>",
        req = self._get(
            f"{self.url}/api/v1/projects/{self.name}", params={"limit": limit}
        )
        if req["status"] == "success":
            return req["data"]
        else:
            raise Exception(req["message"])

    def store(self, data: Dict):
        """
        Store data in the project.

        Arguments:
            data (Dict): The data to store.

        """
        # "/api/v1/projects/<project>",
        req = self._post(f"{self.url}/api/v1/projects/{self.name}", json=data)
        if req["status"] == "success":
            return True
        else:
            raise Exception(req["message"])


class Datatops:
    """
    A client for the Datatops API.

    This class handles getting and setting data.

    """

    # The URL of the Datatops server.
    _url: str

    # ~/.config/datatops/
    _cache_location: pathlib.Path = pathlib.Path.home() / ".config" / "datatops"

    def __init__(self, url: str):
        """
        Create a new Datatops client.

        Args:
            url: The URL of the Datatops server.
        """
        self._url = url

    def _get(self, url: str, **kwargs) -> Dict:
        """
        Make a GET request to the Datatops API.

        Arguments:
            url (str): The url to make the request to.

        Returns:
            Dict: The response from the Datatops API.

        """
        headers = {}
        headers.update(kwargs.pop("headers", {}))
        response = requests.get(url, headers=headers, **kwargs)
        return response.json()

    def _post(self, url: str, **kwargs) -> Dict:
        """
        Make a POST request to the Datatops API.

        Arguments:
            url (str): The url to make the request to.

        Returns:
            Dict: The response from the Datatops API.

        """
        headers = {}
        headers.update(kwargs.pop("headers", {}))
        response = requests.post(url, headers=headers, **kwargs)
        return response.json()

    def get_project(self, name: str, **kwargs) -> Project:
        """
        Get a project by name.

        Args:
            name: The name of the project.

        Returns:
            Project: The project.

        """
        if isinstance(name, pathlib.Path) or name.endswith(".json"):
            return Project.from_json(name, **kwargs)

        # Check if the project is in the cache.
        cache_file = (
            self._cache_location
            / "projects"
            / _namespaced_url(self._url)
            / f"{name}.json"
        )
        if cache_file.exists():
            return Project.from_json(cache_file)

        return Project(name=name, url=self._url, **kwargs)

    def create_project(
        self, name: str, project_creation_secret: Optional[str] = None
    ) -> Project:
        """
        Create a new project.

        Args:
            name: The name of the project.

        Returns:
            Project: The project.

        """
        res = self._post(
            f"{self._url}/api/v1/projects",
            json={"project": name},
            headers={PROJECT_CREATION_SECRET_HEADER: project_creation_secret},
        )
        new_project = Project(
            name=name,
            url=self._url,
            admin_key=res["data"]["admin_key"],
            user_key=res["data"]["user_key"],
        )

        if res["status"] == "success":
            try:
                # Cache the project.
                cache_file = (
                    self._cache_location
                    / "projects"
                    / _namespaced_url(self._url)
                    / f"{name}.json"
                )
                cache_file.parent.mkdir(parents=True, exist_ok=True)
                with open(cache_file, "w") as f:
                    f.write(new_project.to_json())
            except Exception as e:
                print(e)
            return new_project

        else:
            raise Exception(res["message"])
