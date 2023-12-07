import datetime

from flask_restful import Resource, reqparse

from tools import Settings

# Request parser for updating application settings
settings_parser = reqparse.RequestParser()
settings_parser.add_argument("time_period", type=float, required=False)
settings_parser.add_argument("from_time", type=str, required=False)
settings_parser.add_argument("to_time", type=str, required=False)
settings_parser.add_argument("order", type=int, required=False)
settings_parser.add_argument("week_days", type=int, required=False, action="append")
settings_parser.add_argument("max_time", type=float, required=False)
settings_parser.add_argument("max_questions", type=int, required=False)


class SettingsResource(Resource):
    """
    Resource for handling application settings.
    """

    def get(self):
        """
        Get the current application settings.

        Returns:
            tuple: A tuple containing the current application settings and HTTP status code.
        """
        current_settings = Settings().copy()
        current_settings["time_period"] = current_settings["time_period"].total_seconds()
        current_settings["max_time"] = current_settings["max_time"].total_seconds()
        current_settings["from_time"] = current_settings["from_time"].isoformat()
        current_settings["to_time"] = current_settings["to_time"].isoformat()

        return current_settings, 200

    def post(self):
        """
        Update the application settings.

        Returns:
            tuple: A tuple containing the updated application settings and HTTP status code.
        """
        current_settings = Settings()
        args = {k: v for k, v in settings_parser.parse_args().items() if v is not None and k in current_settings}

        if "time_period" in args:
            args["time_period"] = datetime.timedelta(seconds=args["time_period"])
            args["max_time"] = datetime.timedelta(seconds=args["max_time"])
            args["from_time"] = datetime.time.fromisoformat(args["from_time"])
            args["to_time"] = datetime.time.fromisoformat(args["to_time"])

        current_settings.update(args)
        current_settings.update_settings()
        return self.get()
