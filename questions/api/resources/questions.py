import json

from flask_restful import Resource, reqparse
from sqlalchemy import select, update, delete, or_, desc, asc

from api.utils import abort_if_doesnt_exist
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
create_data_parser.add_argument('options', type=str, required=True, action='append')
create_data_parser.add_argument('answer', type=str, required=True)
create_data_parser.add_argument('groups', type=str, required=True, action='append')
create_data_parser.add_argument('level', type=int, required=True)
create_data_parser.add_argument('article_url', type=str, required=False)
create_data_parser.add_argument('type', type=QuestionType, required=False)

sorted_question_data_parser = reqparse.RequestParser()
sorted_question_data_parser.add_argument('search_string', type=str, required=False)
sorted_question_data_parser.add_argument('column_to_order', type=str, required=False)
sorted_question_data_parser.add_argument('descending', type=bool, required=False)


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
    def post(self, question_id):
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
        column_to_order = args['column_to_order']
        descending = args['descending']

        if descending:
            column_to_order = desc(column_to_order)

        with create_session() as db:
            if search_string != "" or column_to_order != "":
                questions = db.scalars(select(Question).
                                       where(or_(Question.text.ilike(f"%{search_string}%"),
                                                 Question.subject.ilike(f"%{search_string}%"),
                                                 Question.options.ilike(f"%{search_string}%"),
                                                 Question.level.ilike(f"%{search_string}%"),
                                                 Question.article_url.ilike(f"%{search_string}%"))).
                                       order_by(column_to_order))
                db_question = [q.to_dict(rules=("-groups.id", "-groups.question_id")) for q in
                               questions]
                for q in db_question:
                    q["options"] = json.loads(q["options"])
            else:
                # Retrieve Question instances from the database and convert them to dictionaries
                db_question = [q.to_dict(rules=("-groups.id", "-groups.question_id")) for q in
                               db.scalars(select(Question))]
                for q in db_question:
                    q["options"] = json.loads(q["options"])

        return db_question, 200

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
