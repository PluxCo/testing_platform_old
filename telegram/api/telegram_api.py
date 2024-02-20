from flask import Flask
from flask_restful import Api

from .resources.message import MessageResource
from .resources.settings import SettingsResource

app = Flask(__name__)
api = Api(app)

api.add_resource(MessageResource, "/message/")
api.add_resource(SettingsResource, "/settings/")
