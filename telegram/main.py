import datetime

from api.telegram_api import app
from bot import bot
from models import db_session
from tools import Settings, setup_logger

default_settings = {
    "pin": "32266",
    "from_time": datetime.time(0),
    "to_time": datetime.time(23, 59),
    "amount_of_questions": 10
}
main_logger = setup_logger(__name__)

if __name__ == "__main__":
    main_logger.info("initializing telegram service")
    Settings().setup("data/settings.json", default_settings)
    db_session.global_init("data/database.db")

    bot = bot.start_bot()
    app.run(debug=False, port=3000, host="0.0.0.0")
