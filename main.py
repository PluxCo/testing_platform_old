import datetime
import math

from models import db_session
import bot
import schedule
from tools import Settings, WeekDays
from web import app as web
from web import socketio

# Environment variables
# ADMIN_PASSWD: password for web panel
# TGTOKEN: token for telegram bot


default_settings = {"tg_pin": "32266",
                    "time_period": datetime.timedelta(days=1),
                    "from_time": datetime.time(0),
                    "to_time": datetime.time(23, 59),
                    "order": 1,
                    "week_days": [WeekDays(d) for d in range(7)],
                    "max_time": datetime.timedelta(minutes=1),
                    "max_questions": 1,
                    }

if __name__ == '__main__':
    Settings().setup("data/settings.stg", default_settings)
    db_session.global_init("data/database.db")

    schedule.Schedule(bot.create_session).from_settings().start()

    bot = bot.start_bot()

    socketio.run(web, host="0.0.0.0", debug=True, use_reloader=False)
