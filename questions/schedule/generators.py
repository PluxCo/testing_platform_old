import abc
import datetime
from typing import Optional

import numpy as np
from sqlalchemy import select, func, or_

from models import db_session
from models.questions import Question, AnswerRecord, AnswerState, QuestionGroupAssociation, QuestionType
from models.users import Person
from tools import Settings


class GeneratorInterface(abc.ABC):
    """
    Abstract base class for question generators.
    """

    @abc.abstractmethod
    def next_bunch(self, person: Person, count=1) -> list[Question | AnswerRecord]:
        """
        Generate a list of questions or question answers.

        Args:
            person (Person): The person for whom questions are generated.
            count (int): The number of questions to generate.

        Returns:
            list[Question | AnswerRecord]: List of generated questions or question answers.
        """
        pass

    @staticmethod
    def _get_planned(db, person: Person) -> list[AnswerRecord]:
        """
        Get planned question answers for a person.

        Args:
            db: Database session.
            person (Person): The person for whom planned question answers are retrieved.

        Returns:
            list[AnswerRecord]: List of planned question answers.
        """
        return db.scalars(select(AnswerRecord).
                          where(AnswerRecord.person_id == person.id,
                                AnswerRecord.ask_time <= datetime.datetime.now(),
                                AnswerRecord.state == AnswerState.NOT_ANSWERED).
                          order_by(AnswerRecord.ask_time)).all()

    @staticmethod
    def _get_person_questions(db, person: Person, planned: list[AnswerRecord]) -> list[Question]:
        """
        Get questions for a person that are not in the planned list.

        Args:
            db: Database session.
            person (Person): The person for whom questions are retrieved.
            planned (list[AnswerRecord]): List of planned question answers.

        Returns:
            list[Question]: List of questions for the person.
        """
        return db.scalars(select(Question).
                          join(Question.groups).
                          where(QuestionGroupAssociation.group_id.in_(pg for pg, pl in person.groups),
                                Question.id.notin_(qa.question_id for qa in planned)).
                          group_by(Question.id)).all()


class SimpleRandomGenerator(GeneratorInterface):
    """
    Simple random question generator.
    """

    def next_bunch(self, person: Person, count=1) -> list[Question | AnswerRecord]:
        """
        Generate a list of questions or question answers using a simple random strategy.

        Args:
            person (Person): The person for whom questions are generated.
            count (int): The number of questions to generate.

        Returns:
            list[Question | AnswerRecord]: List of generated questions or question answers.
        """
        with db_session.create_session() as db:
            # Get planned questions
            planned = self._get_planned(db, person)
            if len(planned) >= count:
                return planned[:count]

            # Get available questions for the person
            person_questions = self._get_person_questions(db, person, planned)

        # Randomly select questions from available ones
        questions = np.random.choice(person_questions,
                                     size=min(count - len(planned), len(person_questions)),
                                     replace=False)

        return list(planned) + list(questions)


class StatRandomGenerator(GeneratorInterface):
    """
    Statistical random question generator.
    """

    def next_bunch(self, person: Person, count=1) -> list[Question | AnswerRecord]:
        """
        Generate a list of questions or question answers using a statistical random strategy.

        Args:
            person (Person): The person for whom questions are generated.
            count (int): The number of questions to generate.

        Returns:
            list[Question | AnswerRecord]: List of generated questions or question answers.
        """
        with db_session.create_session() as db:
            # Get planned questions
            planned = self._get_planned(db, person)
            if len(planned) >= count:
                return planned[:count]

            # Get available questions for the person
            person_questions = self._get_person_questions(db, person, planned)
            probabilities = np.ones(len(person_questions))

            if not person_questions:
                return planned[:count]

            # Calculate probabilities based on user's performance and other factors
            for i, question in enumerate(person_questions):
                question: Question
                correct_count = db.scalar(select(func.count(AnswerRecord.id)).
                                          join(AnswerRecord.question).
                                          where(AnswerRecord.person_id == person.id,
                                                AnswerRecord.question_id == question.id,
                                                AnswerRecord.person_answer == Question.answer))

                if correct_count:
                    last_correct_or_ignored = db.scalar(select(AnswerRecord).
                                                        join(AnswerRecord.question).
                                                        where(AnswerRecord.person_id == person.id,
                                                              AnswerRecord.question_id == question.id,
                                                              or_(AnswerRecord.person_answer == Question.answer,
                                                                  AnswerRecord.state != AnswerState.NOT_ANSWERED)).
                                                        order_by(AnswerRecord.ask_time.desc()))

                    first_answer = db.scalar(select(AnswerRecord).
                                             where(AnswerRecord.person_id == person.id,
                                                   AnswerRecord.question_id == question.id))

                    periods_count = (datetime.datetime.now() - first_answer.ask_time) / Settings()["time_period"]
                    max_target_level = max(
                        gl for pg, gl in person.groups if pg in [x.group_id for x in question.groups])

                    p = (datetime.datetime.now() - last_correct_or_ignored.ask_time).total_seconds() / correct_count
                    p *= np.abs(np.cos(np.pi * np.log2(periods_count + 4))) ** (
                            ((periods_count + 4) ** 2) / 20) + 0.001  # planning questions
                    p *= np.e ** (-0.5 * (max_target_level - question.level) ** 2)  # normal by level

                    probabilities[i] = p
                else:
                    probabilities[i] = None

            db.expunge_all()

        with_val = list(filter(lambda x: not np.isnan(x), probabilities))
        without_val_count = len(person_questions) - len(with_val)

        if with_val:
            increased_avg = (sum(with_val) + without_val_count * max(with_val)) / len(person_questions)
        else:
            increased_avg = 1

        probabilities[np.isnan(probabilities)] = increased_avg
        probabilities /= sum(probabilities)

        # Randomly select questions based on calculated probabilities
        questions = np.random.choice(person_questions,
                                     p=probabilities,
                                     size=min(count - len(planned), len(person_questions)),
                                     replace=False)

        return list(planned) + list(questions)


class Session:
    """
    Session for managing questions and answers for a person.
    """

    def __init__(self, person: Person, max_time, max_questions):
        """
        Initialize a session for a person.

        Args:
            person (Person): The person for whom the session is created.
            max_time: Maximum time for the session.
            max_questions: Maximum number of questions for the session.
        """
        self.person = person
        self.max_time = max_time
        self.max_questions = max_questions

        self._questions: list[AnswerRecord] = []
        self._start_time = datetime.datetime.now()

        self.generator = StatRandomGenerator()

    def generate_questions(self):
        """
        Generate questions for the session.
        """
        self._questions = self.generator.next_bunch(self.person, self.max_questions)
        self._start_time = datetime.datetime.now()

    def next_question(self) -> Optional[AnswerRecord]:
        """
        Get the next question in the session.

        Returns:
            Optional[AnswerRecord]: The next question or None if the session is over.
        """
        if not self._questions or self._start_time + self.max_time < datetime.datetime.now():
            return None

        cur_answer = cur_question = self._questions.pop(0)
        with db_session.create_session() as db:
            if isinstance(cur_question, Question):
                cur_answer = AnswerRecord(question_id=cur_question.id,
                                          person_id=self.person.id,
                                          ask_time=datetime.datetime.now(),
                                          state=AnswerState.NOT_ANSWERED)

                db.add(cur_answer)
                db.commit()

                db.refresh(cur_answer)

            return cur_answer

    @staticmethod
    def mark_question_as_transferred(question_answer: AnswerRecord) -> None:
        """
        Mark a question answer as transferred.

        Args:
            question_answer (AnswerRecord): The question answer to mark as transferred.
        """
        with db_session.create_session() as db:
            question_answer = db.get(AnswerRecord, question_answer.id)
            question_answer.state = AnswerState.TRANSFERRED

            if question_answer.ask_time is None:
                question_answer.ask_time = datetime.datetime.now()

            db.commit()

    @staticmethod
    def register_answer(question_answer: AnswerRecord, user_answer: str):
        """
        Register an answer for a question.

        Args:
            question_answer (AnswerRecord): The question answer for which the user is providing an answer.
            user_answer: The user's answer to the question.
        """
        with db_session.create_session() as db:
            question_answer = db.get(AnswerRecord, question_answer.id)

            if user_answer is not None:
                question_answer.person_answer = user_answer
                question_answer.state = AnswerState.ANSWERED
                question_answer.answer_time = datetime.datetime.now()
                question_answer.calculate_points()

                db.commit()
                db.refresh(question_answer)
            return question_answer
