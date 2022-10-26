import abc
import random
import string
from typing import Dict, Optional
import uuid


def generate_new_user_key() -> str:
    """
    Generates a new alphanumeric user key (all lowercase) of length 8.

    Returns:
        str: The new user key.
    """
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=8))


def generate_new_admin_key() -> str:
    """
    Generates a new UUID admin key, prefixed with "a-".

    Returns:
        str: The new admin key.
    """
    return f"a-{uuid.uuid4()}"


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
