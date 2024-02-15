import datetime

import requests
import json

import abc
from bot.models.telegram_types import AnswerType


class MessageResponse:
    def __init__(self, sent_messages):
        self.sent_messages = sent_messages


class SessionInfo:
    def __init__(self, user_id, state):
        self.user_id = user_id
        self.state = state


class MessageInfo:
    def __init__(self, message_id, session: SessionInfo):
        self.message_id = message_id
        self.session = session


class UserAnswer(abc.ABC):
    type = None
    message_id = None


class Button(UserAnswer):
    type = AnswerType.BUTTON.value

    def __init__(self, button_id, message_id):
        self.button_id = button_id
        self.message_id = message_id


class Message(UserAnswer):
    type = AnswerType.MESSAGE.value

    def __init__(self, text, message_id):
        self.text = text
        self.message_id = message_id


class Reply(UserAnswer):
    type = AnswerType.REPLY.value

    def __init__(self, text, message_id, reply_to):
        self.text = text
        self.message_id = message_id
        self.reply_to = reply_to


class Webhook:
    def __init__(self, user_answer: UserAnswer, session_info: SessionInfo):
        self.user_answer = user_answer
        self.session_info = session_info

    def post(self, webhook):
        try:
            r = requests.post(webhook,
                              json=json.loads(json.dumps(self, default=lambda o: o.__dict__, sort_keys=True))).json()
            return bool(r["clear_buttons"])
        except:
            return False
