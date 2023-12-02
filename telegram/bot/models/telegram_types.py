import enum
import uuid


class MessageType(enum.Enum):
    SIMPLE = 0
    WITH_BUTTONS = 1
    MOTIVATION = 2


class Person:
    def __init__(self):
        self.full_name = None
        self.user_name = str(uuid.uuid4())
        self.groups = []
        self.group_levels = {}
        self.password = str(uuid.uuid4())

    def to_json(self):
        person_info = {"user": {"fullName": self.full_name, "username": self.user_name, "password": self.password,
                                "memberships": [], "data": {}}}

        person_info["user"]["data"]["groupLevels"] = []
        for group in self.groups:
            person_info["user"]["memberships"].append({"groupId": group})

            person_info["user"]["data"]["groupLevels"].append(
                {"groupId": group, "level": self.group_levels[group]})

        return person_info
