import datetime
import enum
import logging
import os

import requests

from data_accessors.auth_accessor import GroupsDAO


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
        PENDING (int): The answer has been provided.
        ANSWERED (int): The answer has been provided and verified.
    """
    NOT_ANSWERED = 0
    TRANSFERRED = 1
    PENDING = 3
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

    def to_dict(self, only: tuple[str] | None = None):
        obj = self.__dict__.copy()
        obj.update({"type": self.type.name})
        if only is not None:
            obj = {key: obj[key] for key in only}
        return obj


class QuestionsDAO:
    __resource = '{}/question/'
    __host = os.getenv("QUESTIONS_URL", "http://localhost:3000")

    @staticmethod
    def set_host(resource: str):
        QuestionsDAO.__host = resource

    @staticmethod
    def _construct(resp):
        q = Question(resp["id"], resp["text"], resp["subject"], resp["options"],
                     resp["answer"], resp["groups"],
                     resp["level"], resp["article_url"],
                     QuestionType(resp["type"]))
        return q

    @staticmethod
    def get_question(question_id: int) -> Question:
        resp = requests.get(QuestionsDAO.__resource.format(QuestionsDAO.__host) + str(question_id)).json()

        question_groups = []

        for group in resp["groups"]:
            question_groups.append(GroupsDAO.get_group(group["group_id"]).label)

        resp["groups"] = question_groups

        return QuestionsDAO._construct(resp)

    @staticmethod
    def get_questions(search_string="", column_to_order="", descending=False):
        resp = requests.get(QuestionsDAO.__resource.format(QuestionsDAO.__host),
                            json={"search_string": search_string, "column_to_order": column_to_order,
                                  "descending": descending})

        if resp.status_code != 200:
            raise Exception(resp.status_code, resp.text)

        resp = resp.json()

        group_ids = {g["group_id"] for q in resp for g in q["groups"]}
        group_names = {}

        for g_id in group_ids:
            group_names[g_id] = GroupsDAO.get_group(g_id).label

        for q in resp:
            q["groups"] = [group_names[group["group_id"]] for group in q["groups"]]

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

    @staticmethod
    def update_question(question: Question):
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

        resp = requests.post(QuestionsDAO.__resource.format(QuestionsDAO.__host) + f'/{question.id}', json=req)

        return '', resp.status_code

    @staticmethod
    def delete_question(question_id: int):
        resp = requests.delete(QuestionsDAO.__resource.format(QuestionsDAO.__host) + f'/{question_id}')

        return resp.status_code


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


class AnswerRecord:
    def __init__(self, r_id: int,
                 question_id: int,
                 person_id: str,
                 person_answer: str,
                 answer_time: datetime.datetime | None,
                 ask_time: datetime.datetime,
                 state: AnswerState,
                 points: float):
        self.r_id = r_id
        self.question_id = question_id
        self.person_id = person_id
        self.person_answer = person_answer
        self.answer_time = answer_time
        self.ask_time = ask_time
        self.state = state
        self.points = points

        self.question = None

    def to_dict(self, only: tuple[str] | None = None):
        obj = self.__dict__.copy()
        obj.update({"answer_time": self.answer_time.isoformat() if self.answer_time else None})
        obj.update({"ask_time": self.ask_time.isoformat()})
        obj.update({"state": self.state.name})
        if only is not None:
            obj = {key: obj[key] for key in only}
        return obj


class AnswerRecordDAO:
    __resource = '{}/answer/'
    __host = os.getenv("QUESTIONS_URL", "http://localhost:3000")

    @staticmethod
    def set_host(resource: str):
        AnswerRecordDAO.__host = resource

    @staticmethod
    def _construct(resp):
        q = AnswerRecord(resp['id'],
                         resp['question_id'],
                         resp['person_id'],
                         resp['person_answer'],
                         datetime.datetime.fromisoformat(resp['answer_time']) if resp['answer_time'] else None,
                         datetime.datetime.fromisoformat(resp['ask_time']),
                         AnswerState(resp['state']),
                         resp['points'])

        return q

    @staticmethod
    def get_all_records():
        for item in requests.get(AnswerRecordDAO.__resource.format(AnswerRecordDAO.__host), json={}).json()["answers"]:
            yield AnswerRecordDAO._construct(item)

    @staticmethod
    def plan_question(question_id, person_id, ask_time):
        req = {"question_id": question_id,
               "person_id": person_id,
               "ask_time": ask_time.isoformat()}

        resp = requests.post(AnswerRecordDAO.__resource.format(AnswerRecordDAO.__host), json=req)

        if resp.status_code != 200:
            raise Exception(resp.status_code, resp.text)

    @staticmethod
    def get_records(question_id=None, person_id=None, order="desc", order_by="ask_time", count=-1, offset=0,
                    only_open=False, state: AnswerState = None):
        req = {
            "answer": {
                "question_id": question_id,
                "person_id": person_id
            },
            "order": order,
            "orderBy": order_by,
            "resultsCount": count,
            "offset": offset
        }

        params = {"order": order,
                  "orderBy": order_by,
                  "resultsCount": count,
                  "offset": offset}

        if only_open:
            req["answer"]["question"] = {"type": QuestionType.OPEN.value}

        if state is not None:
            req["answer"]["state"] = state.value

        if question_id is None:
            del req["answer"]["question_id"]
        if person_id is None:
            del req["answer"]["person_id"]

        resp = requests.get(AnswerRecordDAO.__resource.format(AnswerRecordDAO.__host), params=params, json=req)

        if resp.status_code != 200:
            raise Exception(resp.status_code, resp.text)

        resp = resp.json()

        answers = (AnswerRecordDAO._construct(item) for item in resp["answers"])
        total = resp["results_total"]

        return total, answers

    @staticmethod
    def get_record(record_id: int):
        resp = requests.get(AnswerRecordDAO.__resource.format(AnswerRecordDAO.__host) + str(record_id))

        if resp.status_code != 200:
            raise Exception(resp.status_code, resp.text)

        return AnswerRecordDAO._construct(resp.json())

    @staticmethod
    def delete_record(record_id: int):
        resp = requests.delete(AnswerRecordDAO.__resource.format(AnswerRecordDAO.__host) + str(record_id))

        if resp.status_code != 200:
            raise Exception(resp.status_code, resp.text)

        return ''

    @staticmethod
    def grade_answer(record_id: int, points: float):
        resp = requests.patch(AnswerRecordDAO.__resource.format(AnswerRecordDAO.__host) + str(record_id),
                              json={'points': points})

        if resp.status_code != 200:
            raise Exception(resp.status_code, resp.text)

        return AnswerRecordDAO._construct(resp.json())
