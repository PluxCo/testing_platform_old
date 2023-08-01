from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, ARRAY, Table
from sqlalchemy.orm import relationship, mapped_column

from .db_session import SqlAlchemyBase


class PersonGroupAssociation(SqlAlchemyBase):
    __tablename__ = "person_to_group"

    person_id = Column(ForeignKey("persons.id"), primary_key=True)
    group_id = Column(ForeignKey("person_groups.id"), primary_key=True)
    target_level = Column(Integer)


class PersonGroup(SqlAlchemyBase):
    __tablename__ = "person_groups"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True)


class Person(SqlAlchemyBase):
    __tablename__ = 'persons'

    id = Column(Integer, primary_key=True, autoincrement=True)
    full_name = Column(String)
    groups = relationship("PersonGroup", secondary="person_to_group")
    tg_id = Column(Integer, unique=True)
