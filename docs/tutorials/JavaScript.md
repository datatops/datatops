# Using Datatops

## 1. Get a datatops website

Get the URL of a datatops server from your team. You may have one set up for your research lab, or perhaps you have one for this project specifically. When you go to the URL in your browser, you should see something like the following JSON:

```json
{
    "status": "success",
    "version": "#.#.#",
    "message": "Welcome to the Datatops API!",
    "server_time": 1234567890
}
```

For the rest of this document, we will assume that the URL is `https://example-datatops.com`.

## 2. Get project credentials

In order to use Datatops, you will need to have two sets of credentials — a user key and an admin key. The user key allows the bearer to WRITE data. The admin key allows the bearer to READ and WRITE data. You, as the owner of the data, will be the admin. Your app users will be the... users! Make sure you do not include the admin key in ANY public-facing code, even if it's invisible. Searching for secret access codes in the source-code of websites is possible and common!

There are two ways that you might get credentials for your Datatops database: (1) Your team may already have a project set up and they will give you the keys; or (2) you can create a new project and get brand new keys. If you already have keys, you can skip step 2.5. Otherwise, follow along below:

## 2.5 Creating a new project

You will need to install the Datatops Python library in order to create a new project. To follow along, see the tutorial on creating a new project [here](New-Projects.md).

