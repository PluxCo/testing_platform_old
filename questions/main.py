import datetime

from api import app as flask_app
from models import db_session
from schedule.schedule import Schedule
from tools import Settings

default_settings = {"time_period": datetime.timedelta(seconds=30),
                    "from_time": datetime.time(0),
                    "to_time": datetime.time(23, 59),
                    "order": 1,
                    "week_days": [d for d in range(7)],
                    "max_time": datetime.timedelta(minutes=1),
                    "max_questions": 1,
                    }

if __name__ == '__main__':
    Settings().setup("data/settings.stg", default_settings)
    db_session.global_init("data/database.db")

    Schedule(lambda x: 0).from_settings().start()

    flask_app.run(host="0.0.0.0", debug=False, port=3000)
