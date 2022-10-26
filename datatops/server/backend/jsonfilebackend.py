import json
import pathlib
from typing import Dict, Optional, Union

from .backend import (
    DatatopsServerBackend,
    generate_new_user_key,
    generate_new_admin_key,
)


class JSONFileBackend(DatatopsServerBackend):
    """
    A backend that stores data in JSON files on disk.

    Note that this is not thread-safe and not scalable, so it should never be
    used for production workloads. It is intended for testing and development
    purposes only.

    """

    def __init__(self, path: pathlib.Path):
        """
        Create a new JSONFileBackend.

        Arguments:
            path (pathlib.Path): The path to the directory to store data in.

        """
        path = pathlib.Path(path)
        self.path = path
        self.path.mkdir(parents=True, exist_ok=True)

    def _read_json(self, path: pathlib.Path):
        with open(path, "r") as f:
            return json.load(f)

    def _write_json(self, path: pathlib.Path, data: Dict):
        with open(path, "w") as f:
            json.dump(data, f)

    def _project_exists(self, project: str):
        return (self.path / (project + ".json")).exists()

    def create_project(self, project: str) -> Union[dict, bool]:
        """
        Create a new project.

        Arguments:
            project (str): The name of the project.

        Returns:
            dict: The new project, with name, and user/admin keys.
            bool: False if the project already exists.

        """
        project_path = self.path / (project + ".json")
        if project_path.exists():
            return False
        self._write_json(project_path, {"records": []})
        # Add the project to the list of projects.
        project_dict = {
            "name": project,
            "user_key": generate_new_user_key(),
            "admin_key": generate_new_admin_key(),
        }
        projects_path = self.path / "projects.json"
        if projects_path.exists():
            projects = self._read_json(projects_path)["projects"]
        else:
            projects = []
        projects.append(project_dict)
        self._write_json(projects_path, {"projects": projects})
        return project_dict

    def store(
        self,
        project: str,
        user_key: Optional[str],
        admin_key: Optional[str],
        data: Dict,
    ):
        """
        Store a new data payload in the database.

        Arguments:
            project (str): The name of the project.
            user_key (str): The user key.
            admin_key (str): The admin key.
            data (dict): The data payload.

        Returns:
            bool: True if the data was stored, False if the user is not authorized.

        """
        if not self.is_authorized_to_write(project, user_key, admin_key):
            return False
        project_path = self.path / (project + ".json")
        project_data = self._read_json(project_path)
        project_data["records"].append(data)
        self._write_json(project_path, project_data)
        return True

    def list_data(
        self,
        project: str,
        user_key: Optional[str],
        admin_key: Optional[str],
        limit: Optional[int],
    ):
        """
        List the data in a project.

        Arguments:
            project (str): The name of the project.
            user_key (str): The user key.
            admin_key (str): The admin key.
            limit (int): The maximum number of records to return.

        Returns:
            list: The data records.

        """
        if self._project_exists(project) and self.is_authorized_to_read(
            project, user_key, admin_key
        ):
            project_path = self.path / (project + ".json")
            project_data = self._read_json(project_path)
            if limit is None:
                return project_data["records"]
            else:
                return project_data["records"][:limit]

    def list_projects(self):
        """
        List the projects.

        Returns:
            list: The projects.

        """
        projects_path = self.path / "projects.json"
        if projects_path.exists():
            return [p["name"] for p in self._read_json(projects_path)["projects"]]
        else:
            return []

    def is_authorized_to_write(
        self, project: str, user_key: Optional[str], admin_key: Optional[str]
    ):
        """
        Check if a user is authorized to write to a project.

        Arguments:
            project (str): The name of the project.
            user_key (str): The user key.
            admin_key (str): The admin key.

        Returns:
            bool: True if the user is authorized to write to the project.

        """
        if self._project_exists(project):
            project_path = self.path / "projects.json"
            project_data = self._read_json(project_path)
            for p in project_data["projects"]:
                if p["name"] == project:
                    return p["user_key"] == user_key or p["admin_key"] == admin_key
        return False

    def is_authorized_to_read(
        self, project: str, user_key: Optional[str], admin_key: Optional[str]
    ):
        """
        Check if a user is authorized to read a project.

        Arguments:
            project (str): The name of the project.
            user_key (str): The user key.
            admin_key (str): The admin key.

        Returns:
            bool: True if the user is authorized to read the project.

        """
        if self._project_exists(project):
            project_path = self.path / "projects.json"
            project_data = self._read_json(project_path)
            for p in project_data["projects"]:
                if p["name"] == project:
                    return p["user_key"] == user_key or p["admin_key"] == admin_key
        return False

    def delete_project(self, project: str, admin_key: Optional[str]):
        raise NotImplementedError()
