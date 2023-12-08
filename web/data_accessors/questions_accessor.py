import datetime
import enum

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
    __host = ""

    @staticmethod
    def set_host(resource: str):
        QuestionsDAO.__host = resource

    @staticmethod
    def _construct(resp):
        q = Question(resp["id"], resp["text"], resp["subject"], resp["options"],
                     resp["answer"], [g["group_id"] for g in resp["groups"]],
                     resp["level"], resp["article_url"])
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
            "type": question.type
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
    __host = ""

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
