from sqlalchemy import Column, String, Integer
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy_serializer import SerializerMixin

from .db_session import SqlAlchemyBase


class MessageModel(SqlAlchemyBase, SerializerMixin):
    __tablename__ = "messages"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tg_id = Column(Integer)
    message_id = Column(String)
    webhook = Column(String)
    message_type = Column(Integer)
