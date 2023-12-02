import requests


class Question:
    def __init__(self, q_id: int,
                 text: str,
                 subject: str,
                 options: list[str],
                 answer: int,
                 groups: list[str],
                 level: int,
                 article: str):
        self.id = q_id
        self.text = text
        self.subject = subject
        self.options = options
        self.answer = answer
        self.groups = groups
        self.level = level
        self.article = article


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
            "article_url": question.article
        }
        resp = requests.post(QuestionsDAO.__resource.format(QuestionsDAO.__host), json=req)
