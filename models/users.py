from typing import List

from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship, mapped_column, Mapped
from sqlalchemy_serializer import SerializerMixin

from .db_session import SqlAlchemyBase


class PersonGroupAssociation(SqlAlchemyBase):
    __tablename__ = "person_to_group"

    person_id: Mapped[int] = mapped_column(ForeignKey("persons.id"), primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("person_groups.id"), primary_key=True)
    target_level: Mapped[int] = mapped_column(default=1)


class PersonGroup(SqlAlchemyBase, SerializerMixin):
    __tablename__ = "person_groups"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(unique=True)


class Person(SqlAlchemyBase):
    __tablename__ = 'persons'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    full_name: Mapped[str]
    groups: Mapped[List["PersonGroup"]] = relationship(secondary="person_to_group")
    is_paused: Mapped[bool] = mapped_column(default=False)
    tg_id: Mapped[int] = mapped_column(unique=True)
