import bot
from api.telegram_api import app
from models import db_session
from tools import Settings

default_settings = {"pin": "32266"}

if __name__ == "__main__":
    Settings().setup("data/settings.json", default_settings)
    db_session.global_init("data/database.db")

    bot = bot.start_bot()
    app.run(debug=False, port=3000)
