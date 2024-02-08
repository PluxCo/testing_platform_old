import enum
import uuid
import abc
import json


class MessageType(enum.Enum):
    SIMPLE = 0
    WITH_BUTTONS = 1
    MOTIVATION = 2


class AnswerType(enum.Enum):
    """
    Enumeration representing different types of answers.
    """
    BUTTON = 0
    MESSAGE = 1
    REPLY = 2


class SessionState(enum.Enum):
    """
    Enumeration representing different states of sessions.
    """
    PENDING = 0
    OPEN = 1
    CLOSE = 2


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


class Message(abc.ABC):
    user_id = None
    type = None


class SimpleMessage(Message):

    def __init__(self, dictionary_obj: dict):
        self.type = MessageType.SIMPLE.value
        self.user_id = dictionary_obj["user_id"]
        self.text = dictionary_obj["text"]


class MessageWithButtons(Message):

    def __init__(self, dictionary_obj: dict):
        self.type = MessageType.WITH_BUTTONS.value
        self.user_id = dictionary_obj["user_id"]
        self.text = dictionary_obj["text"]
        self.buttons = dictionary_obj["buttons"]


class Motivation(Message):

    def __init__(self, dictionary_obj: dict):
        self.type = MessageType.MOTIVATION.value

        self.user_id = dictionary_obj["user_id"]
        self.text = dictionary_obj["text"]

