import json

from flask_restful import Resource, reqparse
from sqlalchemy import select, distinct

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


class UserStatisticsResource(Resource):
    # FIXME: Fix this weird and very weird statistics
    def get(self, person_id):
        person = Person.get_person(person_id)
        subject_stat = []
        bar_stat = [[], [], []]

        with db_session.create_session() as db:
            person_subjects = db.scalars(select(distinct(Question.subject)).join(Question.groups).
                                         where(QuestionGroupAssociation.group_id.in_(pg[0] for pg in person.groups)))

            for name in person_subjects:
                all_questions = db.scalars(select(Question).
                                           join(Question.groups).
                                           where(Question.subject == name,
                                                 QuestionGroupAssociation.group_id.in_(pg[0] for pg in person.groups)).
                                           group_by(Question.id)).all()

                correct_count = 0
                correct_count_by_level = {}
                answered_count = 0
                answered_count_by_level = {}
                questions_count = len(all_questions)
                person_answers = []

                for current_question in all_questions:
                    answers = db.scalars(select(AnswerRecord).
                                         where(AnswerRecord.person_id == person.id,
                                               AnswerRecord.question_id == current_question.id,
                                               AnswerRecord.state != AnswerState.NOT_ANSWERED).
                                         order_by(AnswerRecord.ask_time)).all()

                    question_correct_count = len([1 for a in answers if a.person_answer == current_question.answer])
                    question_incorrect_count = len(answers) - question_correct_count

                    answer_state = "NOT_ANSWERED"
                    if answers:
                        answered_count += 1

                        if answers[-1].question.level not in answered_count_by_level.keys():
                            answered_count_by_level[answers[-1].question.level] = 0
                            correct_count_by_level[answers[-1].question.level] = 0

                        answered_count_by_level[answers[-1].question.level] += 1

                        if answers[-1].state == AnswerState.TRANSFERRED:
                            answer_state = "IGNORED"
                        elif answers[-1].question.answer == answers[-1].person_answer:
                            correct_count += 1
                            correct_count_by_level[answers[-1].question.level] += 1
                            answer_state = "CORRECT"
                        else:
                            answer_state = "INCORRECT"

                    person_answers.append({"current_question": current_question.to_dict(),
                                           "answer_state": answer_state,
                                           "question_correct_count": question_correct_count,
                                           "question_incorrect_count": question_incorrect_count})

                subject_stat.append({"name": name,
                                     "correct_count": correct_count,
                                     "answered_count": answered_count,
                                     "questions_count": questions_count,
                                     "person_answers": person_answers})
                progress_by_level = {}

                for level in answered_count_by_level:
                    progress_by_level[level] = round(
                        correct_count_by_level[level] / answered_count_by_level[level] * 100,
                        1)

                bar_stat[0].append(name)
                bar_stat[1].append(progress_by_level)
                if progress_by_level:
                    bar_stat[2].append(max(progress_by_level, key=progress_by_level.get))
            if bar_stat[2]:
                max_level = max(bar_stat[2])
            else:
                max_level = 0
            progress_by_level = []
            for i in range(0, max_level):
                progress_by_level.append([])
                for j in range(len(bar_stat[1])):
                    if (i + 1) in bar_stat[1][j].keys():
                        progress_by_level[i].append(bar_stat[1][j][i + 1])
                    else:
                        progress_by_level[i].append(0)

            bar_data = [bar_stat[0], progress_by_level, max_level]

        resp = {"subject_statistics": subject_stat, "bar_data": bar_data}

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

                    res["answers"].append(a.to_dict(only=("person_answer", "answer_time", "ask_time")))
                    res["answers"][-1]["state"] = answer_state

        return res, 200
