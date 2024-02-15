import enum
import json
import logging
import os

import requests
from flask_restful import Resource, reqparse

from connector.base_connector import ConnectorInterface
from models.questions import AnswerRecord, QuestionType
from schedule.generators import Session


class AnswerType(enum.Enum):
    """
    Enumeration representing different types of answers.
    """
    BUTTON = 0
    MESSAGE = 1
    REPLY = 2


class MessageType(enum.Enum):
    SIMPLE = 0
    WITH_BUTTONS = 1
    MOTIVATION = 2


class SessionState(enum.Enum):
    """
    Enumeration representing different states of sessions.
    """
    PENDING = 0
    OPEN = 1
    CLOSE = 2


class TelegramConnector(ConnectorInterface):
    """
    Connector for interacting with the TelegramService API.
    """
    TG_API = os.getenv("TELEGRAM_API")

    def __init__(self, webhook: str):
        """
        Initialize the TelegramService connector.

        Args:
            webhook (str): The webhook URL for receiving updates from TelegramService.
        """
        TelegramWebhookResource.connector = self
        self.webhook = webhook

        # Dictionary to store active sessions along with the current question answer
        self.alive_sessions: dict[int, tuple[Session, AnswerRecord]] = {}

    def transfer(self, sessions: list[Session]):
        """
        Transfer questions to users through the TelegramService API.

        Args:
            sessions (list[Session]): List of active sessions.
        """
        request = {"webhook": self.webhook,
                   "messages": []}

        message_relation: list[tuple[Session, AnswerRecord]] = []

        for session in sessions:
            current_question = session.next_question()
            if current_question is not None and current_question.question is not None and current_question.question.type == QuestionType.TEST:

                # Prepare the message for sending to TelegramService
                message = {
                    "user_id": current_question.person_id,
                    "type": MessageType.WITH_BUTTONS.value,
                    "text": current_question.question.text,
                    "buttons": ["Не знаю"] + json.loads(current_question.question.options)
                }
                request["messages"].append(message)
                message_relation.append((session, current_question))
            elif current_question is not None and current_question.question is not None and current_question.question.type == QuestionType.OPEN:
                # Prepare the message for sending to TelegramService
                message = {
                    "user_id": current_question.person_id,
                    "text": current_question.question.text,
                    "type": MessageType.SIMPLE.value,
                }
                request["messages"].append(message)
                message_relation.append((session, current_question))
        if not request["messages"]:
            return

        # Send messages to TelegramService
        resp = requests.post(f"{self.TG_API}/message", json=request)
        logging.debug(resp.text)

        # Map message IDs to session-question-answer tuples
        for i, msg in enumerate(resp.json()["sent_messages"]):
            msg_id = msg["message_id"]
            if msg_id is not None:
                self.alive_sessions[msg_id] = message_relation[i]
                session, question = message_relation[i]
                session.mark_question_as_transferred(question)

    def register_answer(self, answer, session_info):
        """
        Register a user's answer received from TelegramService.
        """

        session = None
        match AnswerType(answer["type"]):
            case AnswerType.BUTTON:
                session, question_answer = self.alive_sessions.pop(answer["message_id"])
                registered_answer = session.register_answer(question_answer, str(answer["button_id"]))
                if (registered_answer.points):
                    request = {"webhook": self.webhook,
                               "messages": [{
                                   "user_id": registered_answer.person_id,
                                   "type": MessageType.SIMPLE.value,
                                   "text": "Ответ верный!"
                               }]}
                    requests.post(f"{self.TG_API}/message", json=request)
                else:
                    request = {"webhook": self.webhook,
                               "messages": [{
                                   "user_id": registered_answer.person_id,
                                   "type": MessageType.SIMPLE.value,
                                   "text": "Ответ неверный ;("
                               }]}
                    requests.post(f"{self.TG_API}/message", json=request)

            case AnswerType.REPLY:
                session, question_answer = self.alive_sessions.pop(answer["reply_to"])
                registered_answer = session.register_answer(question_answer, str(answer["text"]))
                request = {"webhook": self.webhook,
                           "messages": [{
                               "user_id": registered_answer.person_id,
                               "type": MessageType.SIMPLE.value,
                               "text": "Понятия не имею правильный ли ответ, но не переживай, я все записал!"
                           }]}
                requests.post(f"{self.TG_API}/message", json=request)

            case AnswerType.MESSAGE:
                # Handle MESSAGE type if needed in the future
                pass

        logging.debug(f"session state: {SessionState(session_info['state'])}")
        match SessionState(session_info["state"]):
            case SessionState.OPEN:
                if session is not None:
                    session.generate_questions()
                    self.transfer([session])
            case SessionState.CLOSE:
                request = {"webhook": self.webhook,
                           "messages": [{
                               "user_id": session.person.id,
                               "type": MessageType.SIMPLE.value,
                               "text": "Всем спасибо, всем пока :)"
                           }]}
                requests.post(f"{self.TG_API}/message", json=request)


class TelegramWebhookResource(Resource):
    """
    Resource for handling incoming webhook requests from TelegramService.
    """
    connector: TelegramConnector = None

    # Request parser for handling incoming answer data
    answer_parser = reqparse.RequestParser()
    answer_parser.add_argument("user_answer", type=dict, required=True)
    answer_parser.add_argument("session_info", type=dict, required=True)

    def post(self):
        """
        Handle incoming POST requests from TelegramService.
        """
        args = self.answer_parser.parse_args()
        logging.debug(f"Received answer request {args}")
        self.connector.register_answer(args["user_answer"], args["session_info"])
        return {"clear_buttons": True}, 200
