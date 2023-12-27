import datetime
import logging
import os
import time
from threading import Thread

from connector.telegram_connector import TelegramConnector
from models.users import Person
from schedule.generators import Session
from tools import Settings


# FIXME: God rewrite this weird Schedule by using basic python module.

class Schedule(Thread):
    def __init__(self, callback):
        super().__init__(daemon=True)
        self._callback = callback

        self._every = None
        self._week_days = None
        self._from_time = None
        self._to_time = None
        Settings().add_update_handler(self.from_settings)

        self.previous_call = None

        self.connector = TelegramConnector(os.getenv("QUESTIONS_URL") + "/webhook/")

    def from_settings(self):
        self._every = Settings()['time_period']
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
                    self.previous_call = now
                    if self._week_days is None or now.weekday() in self._week_days:
                        self.task()
                        self.previous_call = now

            time.sleep(1)

    def task(self):
        try:
            users_sessions = []
            for person in Person.get_all_people():
                session = Session(person)
                session.generate_questions()
                users_sessions.append(session)
                print(person)

            self.connector.transfer(users_sessions)
        except Exception as e:
            logging.error(e)
