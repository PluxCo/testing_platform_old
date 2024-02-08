import datetime

from sqlalchemy import Column, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy_serializer import SerializerMixin
from typing import Optional
from .db_session import SqlAlchemyBase


class Session(SqlAlchemyBase, SerializerMixin):
    __tablename__ = "sessions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_state = Column(Integer)
    user_tg_id = Column(Integer)
    opening_time: Mapped[datetime.datetime]
    amount_of_questions = Column(Integer)
