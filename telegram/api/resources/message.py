from bot.models.telegram_types import Message

from flask_restful import Resource, reqparse

from bot.bot import send_messages
import json

post_message_parser = reqparse.RequestParser()
post_message_parser.add_argument('messages', type=dict, required=True, action='append')
post_message_parser.add_argument('webhook', type=str, required=True)


class MessageResource(Resource):
    def post(self):
        args = post_message_parser.parse_args()
        messages = args["messages"]
        webhook = args["webhook"]

        return json.loads(json.dumps(send_messages(messages, webhook), default=lambda o: o.__dict__)), 200


