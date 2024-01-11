import json
import logging

from flask_restful import Resource, reqparse
from sqlalchemy import select, update, delete, or_, desc, asc, func

from api.utils import abort_if_doesnt_exist, view_parser
from models.db_session import create_session
from models.questions import Question, QuestionGroupAssociation, QuestionType, AnswerRecord

# Request parser for updating question data
update_data_parser = reqparse.RequestParser()
update_data_parser.add_argument('text', type=str, required=False)
update_data_parser.add_argument('subject', type=str, required=False)
update_data_parser.add_argument('options', type=str, required=False, action='append')
update_data_parser.add_argument('answer', type=str, required=False)
update_data_parser.add_argument('groups', type=str, required=False, action='append')
update_data_parser.add_argument('level', type=int, required=False)
update_data_parser.add_argument('article_url', type=str, required=False)
update_data_parser.add_argument('type', type=QuestionType, required=False)

# Request parser for creating a new question
create_data_parser = reqparse.RequestParser()
create_data_parser.add_argument('text', type=str, required=True)
create_data_parser.add_argument('subject', type=str, required=False)
create_data_parser.add_argument('options', type=str, required=False, action='append')
create_data_parser.add_argument('answer', type=str, required=True)
create_data_parser.add_argument('groups', type=str, required=True, action='append')
create_data_parser.add_argument('level', type=int, required=True)
create_data_parser.add_argument('article_url', type=str, required=False)
create_data_parser.add_argument('type', type=QuestionType, required=False)

sorted_question_data_parser = view_parser.copy()
sorted_question_data_parser.add_argument('search_string', type=str, required=False, location="args", default="")


class QuestionResource(Resource):
    """
    Resource for handling individual Question instances.
    """

    @abort_if_doesnt_exist("question_id", Question)
    def get(self, question_id):
        """
        Get the details of a specific Question.

        Args:
            question_id (int): The ID of the Question.

        Returns:
            tuple: A tuple containing the details of the Question and HTTP status code.
        """
        with create_session() as db:
            # Retrieve the Question from the database and convert it to a dictionary
            db_question = db.get(Question, question_id).to_dict(rules=("-groups.id", "-groups.question_id"))
            db_question["options"] = json.loads(db_question["options"])

        return db_question, 200

    @abort_if_doesnt_exist("question_id", Question)
    def patch(self, question_id):
        # TODO: fix update of questions so that after changing options the answers stay correct.
        """
        Update the details of a specific Question.

        Args:
            question_id (int): The ID of the Question.

        Returns:
            tuple: A tuple containing the updated details of the Question and HTTP status code.
        """
        args = update_data_parser.parse_args()
        filtered_args = {k: v for k, v in args.items() if v is not None}

        if "options" in filtered_args:
            filtered_args["options"] = json.dumps(filtered_args["options"], ensure_ascii=True)

        groups = []
        if "groups" in filtered_args:
            groups = [QuestionGroupAssociation(question_id=question_id, group_id=g_id)
                      for g_id in filtered_args["groups"]]
            del filtered_args["groups"]

        with create_session() as db:
            db_question = db.get(Question, question_id)

            db.execute(update(Question).
                       where(Question.id == question_id).
                       values(filtered_args))

            if groups:
                db.execute(delete(QuestionGroupAssociation).
                           where(QuestionGroupAssociation.question_id == question_id))

                db_question.groups.extend(groups)

            if "options" in filtered_args or "answer" in filtered_args:
                answers_to_update = db.scalars(select(AnswerRecord).where(AnswerRecord.question_id == db_question.id))
                for answer in answers_to_update:
                    answer.calculate_points()

            db.commit()

        return self.get(question_id=question_id), 200

    def delete(self, question_id):
        with create_session() as db:
            question = db.get(Question, question_id)
            db.delete(question)
            db.commit()
        return '', 200


class QuestionsListResource(Resource):
    """
    Resource for handling lists of Question instances.
    """

    def get(self, **kwargs):
        """
        Get a list of Question instances.

        Returns:
            tuple: A tuple containing the list of Question instances and HTTP status code.
        """
        args = sorted_question_data_parser.parse_args()

        search_string = args['search_string']

        with create_session() as db:
            total = db.scalar(select(func.count(Question.id)))

            db_req = (select(Question, func.count(Question.id).over())
                      .where(or_(Question.text.ilike(f"%{search_string}%"),
                                 Question.subject.ilike(f"%{search_string}%"),
                                 Question.options.ilike(f"%{search_string}%"),
                                 Question.level.ilike(f"%{search_string}%"),
                                 Question.article_url.ilike(f"%{search_string}%"))))

            db_req = (db_req.order_by(args["orderBy"] if args["order"] == "asc" else desc(args["orderBy"]))
                      .limit(args["resultsCount"])
                      .offset(args["offset"]))

            questions = []
            results_filtered = 0
            for a, results_filtered in db.execute(db_req):
                questions.append(a.to_dict(rules=("-groups.id", "-groups.question_id")))

            for q in questions:
                if q["options"]:
                    q["options"] = json.loads(q["options"])

        return {"results_total": total, "results_count": results_filtered, "questions": questions}, 200

    def post(self, **kwargs):
        """
        Create a new Question instance.

        Returns:
            tuple: A tuple containing the details of the created Question and HTTP status code.
        """
        with create_session() as db:
            args = create_data_parser.parse_args()
            db_question = Question(text=args['text'],
                                   subject=args['subject'],
                                   options=json.dumps(args['options'], ensure_ascii=True),
                                   answer=args['answer'],
                                   level=args['level'],
                                   article_url=args['article_url'],
                                   type=args.get('type', QuestionType.TEST))
            db.add(db_question)
            db.commit()

            for group in args['groups']:
                db_question.groups.append(QuestionGroupAssociation(question_id=db_question.id,
                                                                   group_id=group))
            db.commit()

            return QuestionResource().get(question_id=db_question.id)
