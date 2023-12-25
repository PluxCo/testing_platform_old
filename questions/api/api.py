from flask import Flask
from flask_restful import Api

from api.resources.answer import AnswerResource, AnswerListResource
from api.resources.questions import QuestionResource, QuestionsListResource
from api.resources.settings import SettingsResource
from api.resources.statistics import ShortStatisticsResource, UserStatisticsResource, QuestionStatisticsResourse
from connector.telegram_connector import TelegramWebhookResource

app = Flask(__name__)
api = Api(app)

api.add_resource(QuestionResource, '/question/<int:question_id>')
api.add_resource(QuestionsListResource, '/question/')
api.add_resource(AnswerResource, "/answer/<int:answer_id>")
api.add_resource(AnswerListResource, "/answer/")
api.add_resource(SettingsResource, "/settings/")

api.add_resource(ShortStatisticsResource, "/statistics/user_short")
api.add_resource(UserStatisticsResource, "/statistics/user/<string:person_id>")
api.add_resource(QuestionStatisticsResourse, "/statistics/question/")

api.add_resource(TelegramWebhookResource, "/webhook/")
