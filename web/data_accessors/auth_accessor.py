import os

import requests


class Group:
    def __init__(self, g_id: str,
                 label: str):
        self.id = g_id
        self.label = label


class GroupsDAO:
    __host = os.getenv("FUSIONAUTH_DOMAIN")
    __token = os.getenv("FUSIONAUTH_TOKEN")

    @staticmethod
    def set_host(resource: str, token: str):
        GroupsDAO.__host = resource
        GroupsDAO.__token = token

    @staticmethod
    def _construct(resp):
        q = Group(resp["id"], resp["name"])
        return q

    @staticmethod
    def get_group(group_id: str) -> Group:
        resp = requests.get(f"{GroupsDAO.__host}/api/group/" + str(group_id),
                            headers={"Authorization": GroupsDAO.__token})

        if resp.status_code != 200:
            raise Exception(resp.status_code, resp.text)
        resp = resp.json()

        return GroupsDAO._construct(resp["group"])

    @staticmethod
    def get_all_groups():
        resp = requests.get(f"{GroupsDAO.__host}/api/group/search",
                            headers={"Authorization": GroupsDAO.__token})
        if resp.status_code != 200:
            raise Exception(resp.status_code, resp.text)
        resp = resp.json()

        for g in resp["groups"]:
            yield GroupsDAO._construct(g)

    @staticmethod
    def create_group(group: Group):
        req = {
            "group": {
                "name": group.label
            }
        }

        resp = requests.post(f"{GroupsDAO.__host}/api/group/",
                             json=req,
                             headers={"Authorization": GroupsDAO.__token})


class Person:
    """
    Class representing a person/user with associated groups.
    """

    def __init__(self, user_id: str, full_name: str, groups: list[tuple[str, int]]):
        self.id = user_id
        self.full_name = full_name
        self.groups = groups


class PersonDAO:
    __host = os.getenv("FUSIONAUTH_DOMAIN")
    __token = os.getenv("FUSIONAUTH_TOKEN")

    @staticmethod
    def set_host(resource: str, token: str):
        PersonDAO.__host = resource
        PersonDAO.__token = token

    @staticmethod
    def _construct(resp):
        all_groups = [m["groupId"] for m in resp["memberships"]]
        person_groups = []
        if "groupLevels" in resp["data"]:
            person_groups = [(item["groupId"], item["level"]) for item in resp["data"]["groupLevels"]
                             if item["groupId"] in all_groups]

        q = Person(resp["id"], resp.get("fullName", "Name"), person_groups)
        return q

    @staticmethod
    def get_all_people():
        """
        Static method to retrieve all people/users from FusionAuth.

        Yields:
            Person: A Person instance for each user retrieved.
        """
        resp = requests.get(f"{PersonDAO.__host}/api/user/search?queryString=*",
                            headers={"Authorization": PersonDAO.__token})

        if resp.status_code != 200:
            raise Exception(resp.status_code, resp.text)

        resp = resp.json()

        for person in resp["users"]:
            yield PersonDAO._construct(person)

    @staticmethod
    def get_person(person_id) -> Person:
        resp = requests.get(f"{PersonDAO.__host}/api/user/" + person_id,
                            headers={"Authorization": PersonDAO.__token})

        if resp.status_code != 200:
            raise Exception(resp.status_code, resp.text)

        return PersonDAO._construct(resp.json()['user'])
