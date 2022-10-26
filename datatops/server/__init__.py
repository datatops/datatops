import datetime
import time
from typing import Optional

from flask import Flask, request, jsonify

from .backend import DatatopsServerBackend

from ..config import (
    ADMIN_KEY_HEADER,
    USER_KEY_HEADER,
    DATATOPS_TIMESTAMP_KEY,
    VERSION,
)


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
