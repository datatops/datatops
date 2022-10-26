import time
from typing import Dict, Optional, Union

import boto3
from boto3.dynamodb.conditions import Key

from .backend import (
    DatatopsServerBackend,
    generate_new_user_key,
    generate_new_admin_key,
)
from ...config import DATATOPS_PRIMARY_KEY, DATATOPS_TIMESTAMP_KEY


def _dynamodb_table_exists(table_name: str, client) -> bool:
    """
    Check to see if the DynamoDB table already exists.

    Returns:
        bool: Whether table exists
    """
    existing_tables = client.list_tables()["TableNames"]
    return table_name in existing_tables


def _create_dynamo_table(
    table_name: str,
    client,
    primary_key: str,
    sort_key: Optional[str] = None,
    read_write_units: Optional[int] = None,
):
    """
    Create a DynamoDB table.

    Arguments:
        table_name (str): Name of table to create
        primary_key (str): Primary key of table

        client: DynamoDB client
        read_write_units (int, optional): Read/write units. Defaults to None.

    """
    if read_write_units is not None:
        raise NotImplementedError("Non-on-demand billing is not currently supported.")

    res = client.create_table(
        TableName=table_name,
        KeySchema=[
            {"AttributeName": primary_key, "KeyType": "HASH"},  # Partition key
        ]
        + ([{"AttributeName": sort_key, "KeyType": "RANGE"}] if sort_key else []),
        AttributeDefinitions=[
            {"AttributeName": primary_key, "AttributeType": "S"},
        ]
        + ([{"AttributeName": sort_key, "AttributeType": "N"}] if sort_key else []),
        BillingMode="PAY_PER_REQUEST",
    )
    # Wait for table to be created
    client.get_waiter("table_exists").wait(TableName=table_name)
    return res


class DynamoDBBackend(DatatopsServerBackend):
    """
    A backend that stores data in a DynamoDB table.

    """

    def __init__(
        self,
        data_table_name: str,
        project_table_name: str = "datatops_project_list",
        region_name: str = "us-east-1",
        **kwargs,
    ):
        self.data_table_name = data_table_name
        self.project_table_name = project_table_name
        self.region_name = region_name
        self.dynamodb_client = boto3.client(
            "dynamodb", region_name=region_name, **kwargs
        )
        self.dynamodb_resource = boto3.resource(
            "dynamodb", region_name=region_name, **kwargs
        )

        if not _dynamodb_table_exists(self.data_table_name, self.dynamodb_client):
            _create_dynamo_table(
                self.data_table_name,
                self.dynamodb_client,
                primary_key=DATATOPS_PRIMARY_KEY,
                sort_key=DATATOPS_TIMESTAMP_KEY,
            )

        if not _dynamodb_table_exists(self.project_table_name, self.dynamodb_client):
            _create_dynamo_table(
                self.project_table_name,
                self.dynamodb_client,
                primary_key="name",
            )

        # Create a table resource for the data table
        self.data_table = self.dynamodb_resource.Table(self.data_table_name)
        self.project_table = self.dynamodb_resource.Table(self.project_table_name)
        # Wait for table to be created
        self.data_table.wait_until_exists()
        self.project_table.wait_until_exists()

    def _get_project_dict(self, project: str) -> Union[bool, Dict]:
        """
        Get project dict from DynamoDB.

        Arguments:
            project (str): Project name

        Returns:
            Union[bool,Dict]: False if project doesn't exist, otherwise project dict
        """
        res = self.project_table.get_item(Key={"name": project})
        if "Item" not in res:
            return False
        return res["Item"]

    def _teardown_tables_for_debug_only_this_is_so_dangerous_dont_use_this_function(
        self, yes_im_sure: bool = False
    ):
        """
        Delete the data and project tables.

        """
        if not yes_im_sure:
            print("DON'T USE THIS FUNCTION YOU NERD")
            return
        self.data_table.delete()
        self.project_table.delete()

        # Wait for tables to be deleted
        self.data_table.wait_until_not_exists()
        self.project_table.wait_until_not_exists()

    def is_authorized_to_write(
        self, project: str, user_key: Optional[str], admin_key: Optional[str]
    ):
        # Get the project dict from the project table
        project_dict = self._get_project_dict(project)
        if not project_dict:
            return False

        if not isinstance(project_dict, dict):
            raise ValueError(f"Project dict is not a dict (got {project_dict})")

        # Check if the user key is in the project dict
        if user_key is not None and user_key == project_dict.get("user_key"):
            return True
        if admin_key is not None and admin_key == project_dict.get("admin_key"):
            return True

        return False

    def is_authorized_to_read(
        self, project: str, user_key: Optional[str], admin_key: Optional[str]
    ):
        # Get the project dict from the project table
        project_dict = self._get_project_dict(project)
        if not project_dict:
            return False

        if not isinstance(project_dict, dict):
            raise ValueError(f"Project dict is not a dict (got {project_dict})")

        if admin_key is not None and admin_key == project_dict.get("admin_key"):
            return True
        # if project_dict.get("public_read"):
        #     return True

        return False

    def store(
        self,
        project: str,
        user_key: Optional[str],
        admin_key: Optional[str],
        data: Dict,
    ):
        """
        Store a new data entry in the database.

        Arguments:
            project (str): Project name
            user_key (Optional[str]): User key
            admin_key (Optional[str]): Admin key
            data (Dict): Data to store

        Returns:
            bool: True if successful, False if not

        """
        # Check if the user is authorized to write
        if not self.is_authorized_to_write(project, user_key, admin_key):
            return False

        # Add the timestamp
        data[DATATOPS_TIMESTAMP_KEY] = int(time.time())
        data[DATATOPS_PRIMARY_KEY] = project

        # Store the data
        self.data_table.put_item(Item=data)

        return True

    def list_data(
        self,
        project: str,
        user_key: Optional[str],
        admin_key: Optional[str],
        limit: Optional[int],
    ):
        """
        List data entries.

        Arguments:
            project (str): Project name
            user_key (Optional[str]): User key
            admin_key (Optional[str]): Admin key
            limit (Optional[int]): Limit the number of results

        Returns:
            List[Dict]: List of data entries

        """
        # Check if the user is authorized to read
        if not self.is_authorized_to_read(project, user_key, admin_key):
            return []

        res = self.data_table.query(
            KeyConditionExpression=Key(DATATOPS_PRIMARY_KEY).eq(project),
            **({"Limit": limit} if limit is not None else {}),
        )
        return res["Items"]

    def list_projects(self):
        raise NotImplementedError()

    def create_project(self, project: str):
        """
        Create a new project.

        Arguments:
            project (str): Project name

        Returns:
            dict: Project dict

        """
        # Check if the project already exists
        if self._get_project_dict(project):
            return False

        project_dict = {
            "name": project,
            "user_key": generate_new_user_key(),
            "admin_key": generate_new_admin_key(),
        }

        # Create the project
        self.project_table.put_item(Item=project_dict)

        return project_dict

    def delete_project(self, project: str, admin_key: Optional[str]):
        raise NotImplementedError()
