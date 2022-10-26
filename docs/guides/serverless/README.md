# Serverless Deployments

This guide will walk you through deploying a serverless application to AWS Lambda using Zappa.

## Prerequisites

-   Install `zappa` and `boto3`:

```bash
pip install zappa boto3
```

-   Create an AWS account and configure your credentials. See [AWS Credentials](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-configure.html) for more information.

## Datatops Client

```python
from datatops.server import DatatopsServer
from datatops.server.backend.dynamodbbackend import DynamoDBBackend

DatatopsServer(
    backend=DynamoDBBackend(
        "datatops_data_table",
        "datatops_project_list"
    ),
).run(port=5001)
```
