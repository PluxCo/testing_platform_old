import datetime
import enum
from typing import List, Optional

from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship, backref, mapped_column, Mapped
from sqlalchemy_serializer import SerializerMixin

from .db_session import SqlAlchemyBase
from .users import PersonGroup, Person


class AnswerState(enum.Enum):
    NOT_ANSWERED = 0
    TRANSFERRED = 1
    ANSWERED = 2


class QuestionGroupAssociation(SqlAlchemyBase):
    __tablename__ = "question_to_group"

    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id"), primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("person_groups.id"), primary_key=True)


class Question(SqlAlchemyBase, SerializerMixin):
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    text: Mapped[str]
    subject: Mapped[Optional[str]]
    options: Mapped[str]
    answer: Mapped[int]
    groups: Mapped[List["PersonGroup"]] = relationship(secondary="question_to_group")
    level: Mapped[int]
    article_url: Mapped[Optional[str]]


class QuestionAnswer(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'answers'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id"))
    question: Mapped["Question"] = relationship(backref="answers")
    person_id: Mapped[int] = mapped_column(ForeignKey("persons.id"))
    person_answer: Mapped[Optional[int]]
    answer_time: Mapped[Optional[datetime.datetime]]
    ask_time: Mapped[datetime.datetime] = mapped_column()
    state: Mapped[AnswerState]

    person: Mapped["Person"] = relationship(backref=backref("answers", order_by=ask_time))
