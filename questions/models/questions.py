import datetime
import enum
from typing import List, Optional

import requests
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship, mapped_column, Mapped
from sqlalchemy_serializer import SerializerMixin

from .db_session import SqlAlchemyBase


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


class QuestionType(enum.Enum):
    """
    Enumeration representing the type of AnswerRecord.

    Attributes:
        TEST (int): The question suggests answer in a test form.
        OPEN (int): The question suggest answer in a text form.
    """
    TEST = 0
    OPEN = 1


class QuestionGroupAssociation(SqlAlchemyBase, SerializerMixin):
    """
    Association table between questions and groups.

    Attributes:
        id (int): The primary key of the association.
        question_id (int): Foreign key referencing the questions table.
        group_id (str): The ID of the group associated with the question.
    """
    __tablename__ = "question_to_group"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id"))
    group_id: Mapped[str] = mapped_column()


class Question(SqlAlchemyBase, SerializerMixin):
    """
    Represents a question.

    Attributes:
        id (int): The primary key of the question.
        text (str): The text of the question.
        subject (Optional[str]): The subject of the question (optional).
        options (str): JSON-encoded options for the question.
        answer (str): The correct answer to the question.
        groups (List[QuestionGroupAssociation]): The groups associated with the question.
        level (int): The difficulty level of the question.
        article_url (Optional[str]): URL to an article related to the question (optional).
        type (QuestionType): The type of the answer (TEST, OPEN)

    """
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    text: Mapped[str]
    subject: Mapped[Optional[str]]
    options: Mapped[str]
    answer: Mapped[str]
    groups: Mapped[List[QuestionGroupAssociation]] = relationship(cascade='all, delete-orphan')
    level: Mapped[int]
    article_url: Mapped[Optional[str]]
    type: Mapped[QuestionType] = mapped_column(default=QuestionType.TEST)


class AnswerRecord(SqlAlchemyBase, SerializerMixin):
    """
    Represents an answer to a question.

    Attributes:
        id (int): The primary key of the answer.
        question_id (int): Foreign key referencing the questions table.
        question (Question): Relationship to the corresponding question.
        person_id (str): The ID of the person providing the answer.
        person_answer (Optional[str]): The answer provided by the person (optional).
        answer_time (Optional[datetime.datetime]): The time when the answer was provided (optional).
        ask_time (datetime.datetime): The time when the question was asked.
        state (AnswerState): The state of the answer (NOT_ANSWERED, TRANSFERRED, ANSWERED).
        points (int): Amount of points scored for this answer (from 0 to 1)

    Methods:
        __repr__: Returns a string representation of the AnswerRecord.
    """
    __tablename__ = 'answers'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id"))
    question: Mapped["Question"] = relationship(lazy="joined")
    person_id: Mapped[str] = mapped_column()
    person_answer: Mapped[Optional[str]]
    answer_time: Mapped[Optional[datetime.datetime]]
    ask_time: Mapped[datetime.datetime] = mapped_column()
    state: Mapped[AnswerState]
    points: Mapped[float] = mapped_column(default=0)

    def __repr__(self):
        return f"<AnswerRecord(q_id={self.question_id}, state={self.state}, person_id={self.person_id})>"

    def calculate_points(self):
        match self.question.type:
            case QuestionType.TEST:
                if self.question.answer == self.person_answer:
                    self.points = 1
                else:
                    self.points = 0

            case QuestionType.OPEN:
                # TODO: add adequate calculation of points

                self.points = 0
