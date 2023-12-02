import json

from flask_restful import Resource, reqparse
from sqlalchemy import select, update, delete

from api.utils import abort_if_doesnt_exist
from models.db_session import create_session
from models.questions import Question, QuestionGroupAssociation

# Request parser for updating question data
update_data_parser = reqparse.RequestParser()
update_data_parser.add_argument('text', type=str, required=False)
update_data_parser.add_argument('subject', type=str, required=False)
update_data_parser.add_argument('options', type=str, required=False, action='append')
update_data_parser.add_argument('answer', type=str, required=False)
update_data_parser.add_argument('groups', type=str, required=False, action='append')
update_data_parser.add_argument('level', type=int, required=False)
update_data_parser.add_argument('article_url', type=str, required=False)

# Request parser for creating a new question
create_data_parser = reqparse.RequestParser()
create_data_parser.add_argument('text', type=str, required=True)
create_data_parser.add_argument('subject', type=str, required=False)
create_data_parser.add_argument('options', type=str, required=True, action='append')
create_data_parser.add_argument('answer', type=str, required=True)
create_data_parser.add_argument('groups', type=str, required=True, action='append')
create_data_parser.add_argument('level', type=int, required=True)
create_data_parser.add_argument('article_url', type=str, required=False)


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

            db.commit()

        return self.get(question_id=question_id)


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
        with create_session() as db:
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
                                   article_url=args['article_url'])
            db.add(db_question)
            db.commit()

            for group in args['groups']:
                db_question.groups.append(QuestionGroupAssociation(question_id=db_question.id,
                                                                   group_id=group))
            db.commit()

            return QuestionResource().get(question_id=db_question.id)
