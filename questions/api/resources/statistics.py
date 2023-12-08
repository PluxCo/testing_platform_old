from flask_restful import Resource, reqparse
from sqlalchemy import select

from api.utils import abort_if_doesnt_exist
from models import db_session
from models.db_session import create_session
from models.questions import AnswerRecord, Question, QuestionGroupAssociation, AnswerState
from models.users import Person


class ShortStatisticsResource(Resource):

    def get(self):
        with db_session.create_session() as db:
            persons = Person.get_all_people()
            resp = {}

            for person in persons:
                all_questions = db.scalars(select(Question).
                                           join(Question.groups).
                                           where(QuestionGroupAssociation.group_id.in_(pg for pg, pl in person.groups)).
                                           group_by(Question.id)).all()
                correct_count = 0
                answered_count = 0
                questions_count = len(all_questions)

                # TODO: Optimize db requests

                for current_question in all_questions:
                    answers = db.scalars(select(AnswerRecord).
                                         where(AnswerRecord.person_id == person.id,
                                               AnswerRecord.question_id == current_question.id,
                                               AnswerRecord.state != AnswerState.NOT_ANSWERED).
                                         order_by(AnswerRecord.ask_time)).all()

                    if answers:
                        answered_count += 1
                        correct_count += answers[-1].points

                resp[person.id] = {"correct_count": correct_count,
                                   "answered_count": answered_count,
                                   "questions_count": questions_count}

        return resp, 200
