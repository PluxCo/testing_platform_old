import enum
import json
import os

import requests
from flask_restful import Resource, reqparse

from connector.base_connector import ConnectorInterface
from models.questions import QuestionAnswer
from schedule.generators import Session


class AnswerType(enum.Enum):
    """
    Enumeration representing different types of answers.
    """
    BUTTON = 0
    MESSAGE = 1
    REPLY = 2


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
        self.alive_sessions: dict[int, tuple[Session, QuestionAnswer]] = {}

    def transfer(self, sessions: list[Session]):
        """
        Transfer questions to users through the TelegramService API.

        Args:
            sessions (list[Session]): List of active sessions.
        """
        request = {"webhook": self.webhook,
                   "messages": []}

        message_relation: list[tuple[Session, QuestionAnswer]] = []

        for session in sessions:
            current_question = session.next_question()
            if current_question is not None:
                # Prepare the message for sending to TelegramService
                message = {
                    "user_id": current_question.person_id,
                    "type": "WITH_BUTTONS",
                    "data": {
                        "text": current_question.question.text,
                        "buttons": ["Не знаю"] + json.loads(current_question.question.options)
                    }
                }
                request["messages"].append(message)
                message_relation.append((session, current_question))

        # Send messages to TelegramService
        resp = requests.post(f"{self.TG_API}/message", json=request)

        # Map message IDs to session-question-answer tuples
        for i, message_id in enumerate(resp.json()["message_ids"]):
            if message_id is not None:
                self.alive_sessions[message_id] = message_relation[i]
                session, question = message_relation[i]
                session.mark_question_as_transferred(question)

    def register_answer(self, user_id: str, data_type: AnswerType, data: dict):
        """
        Register a user's answer received from TelegramService.

        Args:
            user_id (str): User ID associated with the answer.
            data_type (AnswerType): Type of answer (BUTTON, REPLY, or MESSAGE).
            data (dict): Data associated with the answer.
        """
        match data_type:
            case AnswerType.BUTTON:
                session, question_answer = self.alive_sessions.pop(data["message_id"])
                session.register_answer(question_answer, data["button_id"])
            case AnswerType.REPLY:
                # Handle REPLY type if needed in the future
                pass
            case AnswerType.MESSAGE:
                # Handle MESSAGE type if needed in the future
                pass


class TelegramWebhookResource(Resource):
    """
    Resource for handling incoming webhook requests from TelegramService.
    """
    connector: TelegramConnector = None

    # Request parser for handling incoming answer data
    answer_parser = reqparse.RequestParser()
    answer_parser.add_argument("user_id", type=str, required=True)
    answer_parser.add_argument("type", type=AnswerType, required=True)
    answer_parser.add_argument("data", type=dict, required=True)

    def post(self):
        """
        Handle incoming POST requests from TelegramService.
        """
        args = self.answer_parser.parse_args()
        self.connector.register_answer(args["user_id"], args["type"], args["data"])
        return '', 200
