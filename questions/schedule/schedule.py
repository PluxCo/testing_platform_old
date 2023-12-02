import datetime
import time
from threading import Thread

from connector.telegram_connector import TelegramConnector
from models.users import Person
from schedule.generators import Session
from tools import Settings


class Schedule(Thread):
    def __init__(self, callback):
        super().__init__(daemon=True)
        self._callback = callback

        self._every = None
        self._order = None  # 1 if time period is calculated first and 0 in other case
        self._week_days = None
        self._from_time = None
        self._to_time = None
        Settings().add_update_handler(self.from_settings)

        self.previous_call = None

        self.connector = TelegramConnector("http://localhost:3000/webhook/")

    def from_settings(self):
        self._every = Settings()['time_period']
        self._order = Settings()['order']
        self._week_days = Settings()['week_days']
        self._from_time = Settings()['from_time']
        self._to_time = Settings()['to_time']

        return self

    def run(self) -> None:
        """The run function of a schedule thread. Note that the order in which you call methods matters.
         on().every() and every().on() play different roles. They in somewhat way mask each-other."""
        while True:
            now = datetime.datetime.now()

            question_for_person = []
            if self._from_time is None or self._from_time <= now.time() <= self._to_time:
                if self.previous_call is None or (now >= self.previous_call + self._every):
                    if self._order == 1:
                        self.previous_call = now
                    if self._week_days is None or now.weekday() in self._week_days:
                        self.task()
                        self.previous_call = now

            time.sleep(1)

    def task(self):
        users_sessions = []
        for person in Person.get_all_people():
            session = Session(person, Settings()["max_time"], Settings()["max_questions"])
            session.generate_questions()
            users_sessions.append(session)
            print(person)

        self.connector.transfer(users_sessions)
