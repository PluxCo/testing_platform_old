import datetime
import enum
import logging
import os

import requests


class QuestionType(enum.Enum):
    """
    Enumeration representing the type of Question.

    Attributes:
        TEST (int): The question suggests answer in a test form.
        OPEN (int): The question suggest answer in a text form.
    """
    TEST = 0
    OPEN = 1


class AnswerState(enum.Enum):
    """
    Enumeration representing the state of AnswerRecord.

    Attributes:
        NOT_ANSWERED (int): The answer has not been provided.
        TRANSFERRED (int): The answer has been transferred to an external system.
        ANSWERED (int): The answer has been provided.
    """
    NOT_ANSWERED = 0
    TRANSFERRED = 1
    ANSWERED = 2


class Question:
    def __init__(self, q_id: int,
                 text: str,
                 subject: str,
                 options: list[str],
                 answer: int,
                 groups: list[str],
                 level: int,
                 article: str,
                 q_type: QuestionType):
        self.id = q_id
        self.text = text
        self.subject = subject
        self.options = options
        self.answer = answer
        self.groups = groups
        self.level = level
        self.article = article
        self.type = q_type


class QuestionsDAO:
    __resource = '{}/question/'
    __host = os.getenv("QUESTIONS_URL", "http://localhost:3000")

    @staticmethod
    def set_host(resource: str):
        QuestionsDAO.__host = resource

    @staticmethod
    def _construct(resp):
        q = Question(resp["id"], resp["text"], resp["subject"], resp["options"],
                     resp["answer"], [g["group_id"] for g in resp["groups"]],
                     resp["level"], resp["article_url"],
                     QuestionType(resp["type"]))
        return q

    @staticmethod
    def get_question(question_id: int) -> Question:
        resp = requests.get(QuestionsDAO.__resource.format(QuestionsDAO.__host) + str(question_id)).json()

        return QuestionsDAO._construct(resp)

    @staticmethod
    def get_all_questions():
        resp = requests.get(QuestionsDAO.__resource.format(QuestionsDAO.__host)).json()
        for q in resp:
            yield QuestionsDAO._construct(q)

    @staticmethod
    def create_question(question: Question):
        req = {
            "text": question.text,
            "subject": question.subject,
            "options": question.options,
            "answer": question.answer,
            "groups": question.groups,
            "level": question.level,
            "article_url": question.article,
            "type": question.type.value
        }

        resp = requests.post(QuestionsDAO.__resource.format(QuestionsDAO.__host), json=req)

        return QuestionsDAO._construct(resp.json())


class Settings:
    def __init__(self, time_period: datetime.timedelta,
                 from_time: datetime.time,
                 to_time: datetime.time,
                 week_days: list[int]):
        self.time_period = time_period
        self.from_time = from_time
        self.to_time = to_time
        self.week_days = week_days


class SettingsDAO:
    __resource = '{}/settings/'
    __host = os.getenv("QUESTIONS_URL", "http://localhost:3000")

    @staticmethod
    def set_host(resource: str):
        SettingsDAO.__host = resource

    @staticmethod
    def _construct(resp):
        q = Settings(datetime.timedelta(seconds=resp["time_period"]),
                     datetime.time.fromisoformat(resp["from_time"]),
                     datetime.time.fromisoformat(resp["to_time"]),
                     resp["week_days"])
        return q

    @staticmethod
    def get_settings() -> Settings:
        resp = requests.get(SettingsDAO.__resource.format(SettingsDAO.__host)).json()
        return SettingsDAO._construct(resp)

    @staticmethod
    def update_settings(settings: Settings):
        req = {
            "time_period": settings.time_period.total_seconds(),
            "from_time": settings.from_time.isoformat(),
            "to_time": settings.to_time.isoformat(),
            "week_days": settings.week_days,
        }

        resp = requests.post(SettingsDAO.__resource.format(SettingsDAO.__host), json=req)

        return SettingsDAO._construct(resp.json())


class StatisticsDAO:
    __resource = '{}/statistics/'
    __host = os.getenv("QUESTIONS_URL", "http://localhost:3000")

    @staticmethod
    def set_host(resource: str):
        StatisticsDAO.__host = resource

    @staticmethod
    def get_short_statistics() -> dict:
        logging.debug(StatisticsDAO.__host)
        return requests.get(StatisticsDAO.__resource.format(StatisticsDAO.__host) + 'user_short').json()

    @staticmethod
    def get_user_statistics(person_id) -> dict:
        resp = requests.get(StatisticsDAO.__resource.format(StatisticsDAO.__host) + 'user/' + person_id)
        return resp.json()

    @staticmethod
    def get_question_statistics(person_id, question_id) -> dict:
        resp = requests.get(
            StatisticsDAO.__resource.format(StatisticsDAO.__host) + f'question/{person_id}/{question_id}')
        return resp.json()


class AnswerRecord:
    def __init__(self, r_id: int,
                 question_id: int,
                 question: Question,
                 person_id: str,
                 person_answer: str,
                 answer_time: datetime.datetime or None,
                 ask_time: datetime.datetime,
                 state: AnswerState,
                 points: float):
        self.r_id = r_id
        self.question_id = question_id
        self.question = question
        self.person_id = person_id
        self.person_answer = person_answer
        self.answer_time = answer_time
        self.ask_time = ask_time
        self.state = state
        self.points = points


class AnswerRecordDAO:
    __resource = '{}/answer/'
    __host = os.getenv("QUESTIONS_URL", "http://localhost:3000")

    @staticmethod
    def set_host(resource: str):
        AnswerRecordDAO.__host = resource

    @staticmethod
    def _construct(resp):
        q = AnswerRecord(resp['id'], resp['question_id'], QuestionsDAO.get_question(resp['question_id']),
                         resp['person_id'], resp['person_answer'],
                         None,
                         datetime.datetime.fromisoformat(resp['ask_time']), AnswerState(resp['state']), resp['points'])
        if resp['answer_time']:
            q.answer_time = datetime.datetime.fromisoformat(resp['answer_time'])

        return q

    @staticmethod
    def get_all_records():
        for item in requests.get(AnswerRecordDAO.__resource.format(AnswerRecordDAO.__host), json={}).json():
            yield AnswerRecordDAO._construct(item)

    @staticmethod
    def plan_question(question_id, person_id, ask_time):
        req = {"question_id": question_id,
               "person_id": person_id,
               "ask_time": ask_time}

        resp = requests.post(AnswerRecordDAO.__resource.format(AnswerRecordDAO.__host), json=req)

        if resp.status_code != 200:
            raise Exception(resp.status_code, resp.text)
