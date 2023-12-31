import json
import logging

from flask_restful import Resource, reqparse
from sqlalchemy import select, distinct, func, case

from data_accessors.auth_accessor import GroupsDAO
from models import db_session
from models.questions import AnswerRecord, Question, QuestionGroupAssociation, AnswerState
from models.users import Person

question_stats_data_parser = reqparse.RequestParser()
question_stats_data_parser.add_argument('question_id', type=str, required=False)
question_stats_data_parser.add_argument('person_id', type=str, required=False)


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

                last_answers = (select(AnswerRecord.id)
                                .where(AnswerRecord.person_id == person.id)
                                .group_by(AnswerRecord.question_id)
                                .having(AnswerRecord.answer_time == func.max(AnswerRecord.answer_time)))

                correct_count = db.scalar(select(func.sum(AnswerRecord.points)).
                                          where(AnswerRecord.id.in_(last_answers)))
                answered_count = db.scalar(select(func.count(AnswerRecord.id)).
                                           where(AnswerRecord.id.in_(last_answers)))
                questions_count = len(all_questions)

                resp[person.id] = {"correct_count": correct_count,
                                   "answered_count": answered_count,
                                   "questions_count": questions_count}

        return resp, 200


class UserStatisticsResource(Resource):
    def get(self, person_id):
        person = Person.get_person(person_id)

        ls_stat = []

        with db_session.create_session() as db:
            person_subjects = (select(distinct(Question.subject)).join(Question.groups).
                               where(QuestionGroupAssociation.group_id.in_(pg[0] for pg in person.groups)))

            last_user_answers = (select(AnswerRecord.id)
                                 .where(AnswerRecord.person_id == person.id)
                                 .group_by(AnswerRecord.question_id)
                                 .having(AnswerRecord.answer_time == func.max(AnswerRecord.answer_time)))

            total_points, total_answered_count = db.execute(select(func.sum(AnswerRecord.points),
                                                                   func.count(AnswerRecord.question_id))
                                                            .where(AnswerRecord.id.in_(last_user_answers))).one()

            # points and answered_count by subjects and levels
            level_subject_info = db.execute(select(Question.level,
                                                   Question.subject,
                                                   func.sum(AnswerRecord.points),
                                                   func.count(AnswerRecord.question_id))
                                            .join(AnswerRecord.question)
                                            .where(AnswerRecord.id.in_(last_user_answers))
                                            .group_by(Question.level, Question.subject)).all()

            questions_count = db.execute(select(Question.level, Question.subject, func.count(distinct(Question.id)))
                                         .join(Question.groups)
                                         .where(QuestionGroupAssociation.group_id.in_(pg[0] for pg in person.groups))
                                         .group_by(Question.level, Question.subject)).all()

            user_question_ids = (select(distinct(Question.id))
                                 .join(Question.groups)
                                 .where(QuestionGroupAssociation.group_id.in_(pg[0] for pg in person.groups)))

            # contains total/last points and answered/transferred counts for all questions that available for user
            questions = db.execute(select(Question,
                                          func.coalesce(func.sum(AnswerRecord.points), 0),
                                          func.count(case((AnswerRecord.state == AnswerState.ANSWERED, 1))),
                                          func.count(case((AnswerRecord.state == AnswerState.TRANSFERRED, 1))),
                                          func.coalesce(
                                              case((AnswerRecord.answer_time == func.max(AnswerRecord.answer_time),
                                                    AnswerRecord.points)), 0)
                                          )
                                   .outerjoin(AnswerRecord, Question.id == AnswerRecord.question_id)
                                   .where((AnswerRecord.person_id == person_id) | (AnswerRecord.person_id == None),
                                          Question.id.in_(user_question_ids))
                                   .group_by(Question.id)).all()

            ls_stat = [{"level": level,
                        "subject": subj,
                        "points": points,
                        "answered_count": count,
                        "questions_count": next(q_c for q_l, q_s, q_c in questions_count
                                                if q_l == level and q_s == subj)}  # that's lmao find O(N^2)
                       for level, subj, points, count in level_subject_info]

            questions_stat = [{"question": q.to_dict(only=("id", "text", "subject", "level")),
                               "total_points": total_points,
                               "last_points": last_points,
                               "answered_count": answered_count,
                               "transferred_count": transferred_count}
                              for q, total_points, answered_count, transferred_count, last_points in questions]

        resp = {"ls": ls_stat,
                "questions": questions_stat,
                "total_point": total_points,
                "total_answered_count": total_answered_count}

        return resp, 200


class QuestionStatisticsResourse(Resource):
    def get(self):
        args = question_stats_data_parser.parse_args()
        person_id = args["person_id"]
        question_id = args["question_id"]
        res = {"question": None, "answers": []}

        with db_session.create_session() as db:
            question = db.get(Question, question_id)

            res["question"] = question.to_dict(
                only=("text", "level", "answer", "id", "groups.group_id", "subject", "article_url"))
            for group in res["question"]["groups"]:
                try:
                    group["name"] = GroupsDAO.get_group(group["group_id"]).label
                except Exception as e:
                    pass

            res["question"]["options"] = json.loads(question.options)

            if person_id != "":
                answers = db.scalars(select(AnswerRecord).
                                     where(AnswerRecord.person_id == person_id,
                                           AnswerRecord.question_id == question_id).
                                     order_by(AnswerRecord.ask_time.desc()))

                for a in answers:
                    a: AnswerRecord
                    if a.state == AnswerState.TRANSFERRED:
                        answer_state = "IGNORED"
                    elif a.state == AnswerState.NOT_ANSWERED:
                        answer_state = "NOT_ANSWERED"
                    elif a.question.answer == a.person_answer:
                        answer_state = "CORRECT"
                    else:
                        answer_state = "INCORRECT"

                    res["answers"].append(a.to_dict(only=("person_answer", "answer_time", "ask_time", "points")))
                    res["answers"][-1]["state"] = answer_state

        return res, 200
