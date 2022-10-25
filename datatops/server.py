import abc
import datetime
import pathlib
import random
import string
import time
from typing import Dict, Optional, Union
import json
import uuid

from flask import Flask, request, jsonify

from .config import (
    ADMIN_KEY_HEADER,
    USER_KEY_HEADER,
    DATATOPS_TIMESTAMP_KEY,
    VERSION,
)


class DatatopsServerBackend(abc.ABC):
    @abc.abstractmethod
    def store(
        self,
        project: str,
        user_key: Optional[str],
        admin_key: Optional[str],
        data: Dict,
    ):
        raise NotImplementedError

    @abc.abstractmethod
    def list_data(
        self,
        project: str,
        user_key: Optional[str],
        admin_key: Optional[str],
        limit: Optional[int],
    ):
        raise NotImplementedError

    @abc.abstractmethod
    def list_projects(self):
        raise NotImplementedError

    @abc.abstractmethod
    def is_authorized_to_write(
        self, project: str, user_key: Optional[str], admin_key: Optional[str]
    ):
        raise NotImplementedError

    @abc.abstractmethod
    def is_authorized_to_read(
        self, project: str, user_key: Optional[str], admin_key: Optional[str]
    ):
        raise NotImplementedError

    @abc.abstractmethod
    def create_project(self, project: str):
        raise NotImplementedError

    @abc.abstractmethod
    def delete_project(self, project: str, admin_key: Optional[str]):
        raise NotImplementedError


def _generate_new_user_key() -> str:
    """
    Generates a new alphanumeric user key (all lowercase) of length 8.

    Returns:
        str: The new user key.
    """
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=8))


def _generate_new_admin_key() -> str:
    """
    Generates a new UUID admin key, prefixed with "a-".

    Returns:
        str: The new admin key.
    """
    return f"a-{uuid.uuid4()}"


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
            "user_key": _generate_new_user_key(),
            "admin_key": _generate_new_admin_key(),
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


class DatatopsServer:
    """
    A server for the Datatops API.

    This handles the HTTP API requests (using Flask) and the database itself,
    using a `DatatopsServerBackend`.

    """

    def __init__(
        self,
        backend: DatatopsServerBackend,
        project_creation_secret: Optional[str] = None,
    ):
        """
        Initialize the server.

        Arguments:
            backend (DatatopsServerBackend): The backend to use.

        """
        self.backend = backend
        self._project_creation_secret = project_creation_secret
        self.app = Flask(__name__)
        self._add_routes()

    def create_project(self, project: str):
        """
        Create a project.

        Arguments:
            project (str): The name of the project.

        Returns:
            dict: The project data.

        """
        return self.backend.create_project(project)

    def store(
        self,
        project: str,
        data: dict,
        user_key: Optional[str],
        admin_key: Optional[str],
    ):
        """
        Store data in a project.

        Arguments:
            project (str): The name of the project.
            data (dict): The data to store.
            user_key (str): The user key.
            admin_key (str): The admin key.

        Returns:
            bool: True if the data was stored.

        """
        data[DATATOPS_TIMESTAMP_KEY] = datetime.datetime.now().isoformat()
        return self.backend.store(project, user_key, admin_key, data)

    def list_data(
        self,
        project: str,
        user_key: Optional[str],
        admin_key: Optional[str],
        limit: Optional[int] = None,
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
        return self.backend.list_data(project, user_key, admin_key, limit)

    def _add_routes(self):
        """
        Add the routes to the Flask app.

        """
        self.app.add_url_rule(
            "/api/v1/projects",
            "create_project",
            self._create_project,
            methods=["POST"],
        )
        self.app.add_url_rule(
            "/api/v1/projects/<project>",
            "store",
            self._store,
            methods=["POST"],
        )
        self.app.add_url_rule(
            "/api/v1/projects/<project>",
            "list_data",
            self._list_data,
            methods=["GET"],
        )

        self.app.add_url_rule(
            "/",
            "index",
            self._index,
            methods=["GET"],
        )

    def _create_project(self):
        """
        Create a project.

        """
        if not request.json:
            return jsonify({"error": "No JSON data"}), 400
        project = request.json.get("project")
        project_creation_secret = request.headers.get("X-Project-Creation-Secret")

        if (
            self._project_creation_secret
            and project_creation_secret != self._project_creation_secret
        ):
            return (
                jsonify({"error": "Project could not be created."}),
                403,
            )

        if project is None:
            return jsonify({"status": "error", "message": "Missing project name."}), 400
        try:
            project_data = self.create_project(project)
            if not project_data:
                return (
                    jsonify(
                        {
                            "status": "error",
                            "message": "Project could not be created. (Maybe it already exists?)",
                        }
                    ),
                    400,
                )
        except ValueError as e:
            return jsonify({"status": "error", "message": str(e)}), 400
        return jsonify({"status": "success", "data": project_data})

    def _store(self, project):
        """
        Store data in a project.

        """
        data = request.json
        user_key = request.headers.get(USER_KEY_HEADER)
        admin_key = request.headers.get(ADMIN_KEY_HEADER)

        if data is None:
            return jsonify({"status": "error", "message": "Missing data."}), 400
        if not self.store(project, data, user_key, admin_key):
            return jsonify({"status": "error", "message": "Not authorized."}), 403
        return jsonify({"status": "success"})

    def _list_data(self, project):
        """
        List the data in a project.

        """
        user_key = request.headers.get(USER_KEY_HEADER)
        admin_key = request.headers.get(ADMIN_KEY_HEADER)
        limit = request.args.get("limit")
        if limit is not None:
            limit = int(limit)
        data = self.list_data(project, user_key, admin_key, limit)
        return jsonify(
            {
                "data": data,
                "status": "success",
            }
        )

    def _index(self):
        """
        The index page.

        """
        return jsonify(
            {
                "status": "success",
                "version": VERSION,
                "message": "Welcome to the Datatops API!",
                "server_time": time.time(),
            }
        )

    def run(self, host: str = "0.0.0.0", port: int = 5000, **kwargs):
        """
        Run the server.

        Arguments:
            host (str): The host to run on.
            port (int): The port to run on.

        """
        self.app.run(host=host, port=port, **kwargs)
