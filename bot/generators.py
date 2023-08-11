import abc
import datetime
from typing import Optional

import numpy as np
from sqlalchemy import select, func, or_

from tools import Settings

from models import db_session
from models.questions import Question, QuestionAnswer, AnswerState
from models.users import Person, PersonGroup, PersonGroupAssociation


class GeneratorInterface(abc.ABC):
    @abc.abstractmethod
    def next_bunch(self, person: Person, count=1) -> list[Question | QuestionAnswer]:
        pass

    @staticmethod
    def _get_planned(db, person: Person) -> list[QuestionAnswer]:
        return db.scalars(select(QuestionAnswer).
                          where(QuestionAnswer.person_id == person.id,
                                QuestionAnswer.ask_time <= datetime.datetime.now(),
                                QuestionAnswer.state == AnswerState.NOT_ANSWERED).
                          order_by(QuestionAnswer.ask_time)).all()

    @staticmethod
    def _get_person_questions(db, person: Person, planned: list[QuestionAnswer]) -> list[Question]:
        return db.scalars(select(Question).
                          join(Question.groups).
                          where(PersonGroup.id.in_(pg.id for pg in person.groups),
                                Question.id.notin_(qa.question_id for qa in planned)).
                          group_by(Question.id)).all()


class SimpleRandomGenerator(GeneratorInterface):
    def next_bunch(self, person: Person, count=1) -> list[Question | QuestionAnswer]:
        with db_session.create_session() as db:
            planned = self._get_planned(db, person)
            if len(planned) >= count:
                return planned[:count]

            person_questions = self._get_person_questions(db, person, planned)

        questions = np.random.choice(person_questions,
                                     size=min(count - len(planned), len(person_questions)),
                                     replace=False)

        return list(planned) + list(questions)


class StatRandomGenerator(GeneratorInterface):
    def next_bunch(self, person: Person, count=1) -> list[Question | QuestionAnswer]:
        with db_session.create_session() as db:
            planned = self._get_planned(db, person)
            if len(planned) >= count:
                return planned[:count]

            person_questions = self._get_person_questions(db, person, planned)
            probabilities = np.ones(len(person_questions))

            if not person_questions:
                return planned[:count]

            for i, question in enumerate(person_questions):
                question: Question
                correct_count = db.scalar(select(func.count(QuestionAnswer.id)).
                                          join(QuestionAnswer.question).
                                          where(QuestionAnswer.person_id == person.id,
                                                QuestionAnswer.question_id == question.id,
                                                QuestionAnswer.person_answer == Question.answer))

                if correct_count:
                    last_correct_or_ignored = db.scalar(select(QuestionAnswer).
                                                        join(QuestionAnswer.question).
                                                        where(QuestionAnswer.person_id == person.id,
                                                              QuestionAnswer.question_id == question.id,
                                                              or_(QuestionAnswer.person_answer == Question.answer,
                                                                  QuestionAnswer.state != AnswerState.NOT_ANSWERED)).
                                                        order_by(QuestionAnswer.ask_time.desc()))

                    first_answer = db.scalar(select(QuestionAnswer).
                                             where(QuestionAnswer.person_id == person.id,
                                                   QuestionAnswer.question_id == question.id))

                    periods_count = (datetime.datetime.now() - first_answer.ask_time) / Settings()["time_period"]

                    max_target_level = db.scalar(select(func.max(PersonGroupAssociation.target_level)).
                                                 where(PersonGroupAssociation.person_id == person.id,
                                                       PersonGroupAssociation.group_id.in_(
                                                           q.id for q in question.groups)))

                    p = (datetime.datetime.now() - last_correct_or_ignored.ask_time).total_seconds() / correct_count
                    p *= np.abs(np.cos(np.pi * np.log2(periods_count + 4))) ** (
                            ((periods_count + 4) ** 2) / 20) + 0.001  # planning questions
                    p *= np.e ** (-0.5 * (max_target_level - question.level) ** 2)  # normal by level

                    probabilities[i] = p
                else:
                    probabilities[i] = None

        with_val = list(filter(lambda x: not np.isnan(x), probabilities))
        without_val_count = len(person_questions) - len(with_val)

        if with_val:
            increased_avg = (sum(with_val) + without_val_count * max(with_val)) / len(person_questions)
        else:
            increased_avg = 1

        probabilities[np.isnan(probabilities)] = increased_avg
        probabilities /= sum(probabilities)

        questions = np.random.choice(person_questions,
                                     p=probabilities,
                                     size=min(count - len(planned), len(person_questions)),
                                     replace=False)

        return list(planned) + list(questions)


class Session:
    def __init__(self, person: Person, max_time, max_questions):
        self.person = person
        self.max_time = max_time
        self.max_questions = max_questions

        self._questions: list[QuestionAnswer] = []
        self._start_time = datetime.datetime.now()

        self.generator = StatRandomGenerator()

    def generate_questions(self):
        self._questions = self.generator.next_bunch(self.person, self.max_questions)
        self._start_time = datetime.datetime.now()

    def next_question(self) -> Optional[QuestionAnswer]:
        if not self._questions or self._start_time + self.max_time < datetime.datetime.now():
            return None

        cur_answer = cur_question = self._questions.pop(0)
        with db_session.create_session() as db:
            if isinstance(cur_question, Question):
                cur_answer = QuestionAnswer(question_id=cur_question.id,
                                            person_id=self.person.id,
                                            ask_time=datetime.datetime.now(),
                                            state=AnswerState.NOT_ANSWERED)

                db.add(cur_answer)
                db.commit()

            return cur_answer
