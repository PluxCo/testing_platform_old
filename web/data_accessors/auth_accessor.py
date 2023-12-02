import requests


class Group:
    def __init__(self, g_id: str,
                 label: str):
        self.id = g_id
        self.label = label


class GroupsDAO:
    __host = ""
    __token = ""

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
