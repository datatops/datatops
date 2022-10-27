# Setting up a new project

To save data to Datatops, you must have a "project" in which the data will live. A project can represent any organizational unit you like: You might have one project for each application you build, or you might choose to have one project per programmer in your team. Or more experienced database users might choose to use one project per traditional database table. No matter what, the setup of a project is the same:

## Installing the Python library

You can install the Datatops Python library from the internet by using pip:

```bash
pip install -U datatops
```

Once you have installed datatops, you should be able to access it in a new Python shell without error:

```python
>>> import datatops
```

## Creating a new project

```python
from datatops import Datatops

dt = Datatops("https://datatops-example.com")
project = dt.create_project("jordans-survey")
```

## Storing credentials

By default, Datatops will save a copy of your credentials in `~/.config/datatops/projects`. That way, the next time you want to access data from that project, you can use the following code:

```python
project = dt.get_project("jordans-survey")
```

If you are not on your own laptop, or you need a copy of the credentials, you can save them like this:

```python
project.save_json("jordans-survey-credentials.json")
```
