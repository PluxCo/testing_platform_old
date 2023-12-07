from flask_restful import Resource, reqparse
from tools import Settings

post_settings_parser = reqparse.RequestParser()
post_settings_parser.add_argument('pin', type=str)


class SettingsResource(Resource):
    def get(self):
        current_settings = Settings().copy()
        return current_settings, 200

    def post(self):
        args = post_settings_parser.parse_args()
        if args['pin'].isdigit():
            current_settings = Settings()
            args = {'pin': args['pin']}
            current_settings.update(args)
            current_settings.update_settings()
            return 200
        else:
            return 404
