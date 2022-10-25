<p align=center>
<img alt="datatops logo" src="https://user-images.githubusercontent.com/693511/197777462-2df2e338-3582-4c92-9475-490e7e159ab7.png" width="150" />
<h1 align=center><b>d a t a t o p s</b></h1>
</p>

Datatops is a super-simple data storage and retrieval tool for small, low-traffic projects.

## Overview

If you are looking for installation instructions, see [Installation](#installation).

## Creating a new project

If you already have a datatops server set up, you can create a new project like this:

```python
from datatops import Datatops

dt = Datatops("https://my-datatops-website.com")
project = dt.create_project("my-survey")
```

This will create a new project called "my-survey" on your datatops server.

The `project` variable has some important details:

```python
>>> print(project)
<Project
    name="my-survey",
    url="https://my-datatops-website.com/projects/my-survey",
    user_key="s9bhn4kd",
    admin_key="a-f4001f00-152a-4a84-8eba-d352b5f00884"
>
```

You will never be shown the `admin_key` again, so make sure to save it somewhere safe. You will need it to read your data and manage the project later.

**IMPORTANT!** By default, datatops will also store newly created projects in the `~/.config/datatops` directory. If you're not on your own computer, **STOP** what you're doing and run this NOW:

```python
project.save_json("datatops_my-survey.json")
```

This will save the project details to a file called `datatops_my-survey.json`.

## Saving data

We will first save data to the project as an admin, and then we will see an example of how to use datatops to store data submitted by users.

### Saving data as an admin

You can use the `project` object to store and retrieve data:

```python
project.store({"name": "Jordan", "breakfast_juice": "grapefruit"})
```

This will store the data in the project. You can store any JSON-serializable data.

### Saving data submitted by users

If you want to allow users to submit data to your project, you can share the `user_key` with them. They can then use the user key to make requests to your datatops server.

#### Saving data in Python

```python
from datatops import Datatops

dt = Datatops("https://my-datatops-website.com")
project = dt.get_project("my-survey", user_key="s9bhn4kd")
project.store({"name": "Jordan", "breakfast_juice": "grapefruit"})
```

#### Saving data in JavaScript

This example is most useful if your users are submitting data from a web app:

```javascript
fetch("https://my-datatops-website.com/projects/my-survey", {
    method: "POST",
    headers: {
        "Content-Type": "application/json",
        "X-Datatops-User-Key": "s9bhn4kd",
    },
    body: JSON.stringify({
        name: "Jordan",
        breakfast_juice: "grapefruit",
    }),
});
```

## Retrieving data

In order to retrieve data, you will need the `admin_key` for the project. If you still have the `project` object from before, you can use that. Otherwise, you can use the `get_project` method:

```python
from datatops import Datatops

dt = Datatops("https://my-datatops-website.com")

# If you're on your own computer and you have the
# project saved in the ~/.config/datatops directory:
project = dt.get_project("my-survey")

# Or, if you saved your own copy of the project details:
project = dt.get_project(json="datatops_my-survey.json")

# Or, if you have the admin key:
project = dt.get_project(
    "my-survey",
    admin_key="a-f4001f00-152a-4a84-8eba-d352b5f00884"
)
```

Once you have the project, you can retrieve the data:

```python
data = project.list_data()
```

## Is datatops right for me?

If you check all of the following boxes (or mostly all of them), then datatops is probably right for you:

-   [ ] I have a project that has no current backend or server
-   [ ] I need to save data
-   [ ] I am not using a database
-   [ ] I am not using authentication or authorization tools
-   [ ] I need to store lots of relatively small (<100kb) records
-   [ ] I will retrieve all (or almost all) of my records at once
-   [ ] My users will never (or almost never) need to retrieve data

## Starting a new server

```python
from datatops.server import DatatopsServer, JSONFileBackend

DatatopsServer(JSONFileBackend(path="mock-projects")).run(port=5001)
```

You can also limit who can create a new project by passing a `project_creation_secret` to the `DatatopsServer` constructor:

```python
DatatopsServer(
    JSONFileBackend(path="mock-projects"),
    project_creation_secret="my-secret",
).run(port=5001)
```

Now in order to be allowed to create a new project, you will need to pass the `project_creation_secret` argument:

```python
dt = Datatops("http://localhost:5001")
dt.create_project(
    "my-survey",
    project_creation_secret="my-secret",
)
```

## Usage example

```python
>>> from datatops import Datatops
>>> dt = Datatops("http://localhost:5001")
>>> proj = dt.create_project("my_project5")
>>> proj.store({"a": 1, "b": 2})
>>> proj.list_data()
```
