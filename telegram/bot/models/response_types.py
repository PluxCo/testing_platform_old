import requests
import json

import abc


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


class Webhook:
    def __init__(self, user_answer, session_info: SessionInfo):
        self.user_answer = user_answer
        self.session_info = session_info

    def post(self, webhook):
        try:
            r = requests.post(webhook, json=json.dumps(self, default=lambda o: o.__dict__, sort_keys=True)).json()
            return bool(r["clear_buttons"])
        except:
            pass


class UserAnswer(abc.ABC):
    pass

