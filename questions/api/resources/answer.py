from flask_restful import Resource, reqparse
from sqlalchemy import select

from api.utils import abort_if_doesnt_exist
from models.db_session import create_session
from models.questions import QuestionAnswer

# Request parser for filtering answer resources based on person_id and question_id
fields_parser = reqparse.RequestParser()
fields_parser.add_argument('person_id', type=str, required=False)
fields_parser.add_argument('question_id', type=int, required=False)


class AnswerResource(Resource):
    """
    Resource for handling individual QuestionAnswer instances.
    """

    @abort_if_doesnt_exist("answer_id", QuestionAnswer)
    def get(self, answer_id):
        """
        Get the details of a specific QuestionAnswer.

        Args:
            answer_id (int): The ID of the QuestionAnswer.

        Returns:
            tuple: A tuple containing the details of the QuestionAnswer and HTTP status code.
        """
        with create_session() as db:
            # Retrieve the QuestionAnswer from the database and convert it to a dictionary
            db_answer = db.get(QuestionAnswer, answer_id).to_dict(rules=("-question",))
        return db_answer, 200


class AnswerListResource(Resource):
    """
    Resource for handling lists of QuestionAnswer instances.
    """

    def get(self):
        """
        Get a list of QuestionAnswer instances based on optional filtering parameters.

        Returns:
            tuple: A tuple containing the list of QuestionAnswer instances and HTTP status code.
        """
        # Parse the filtering parameters from the request
        args = {k: v for k, v in fields_parser.parse_args().items() if v is not None}
        with create_session() as db:
            # Retrieve QuestionAnswer instances from the database based on the filtering parameters
            answers = [a.to_dict(rules=("-question",)) for a in db.scalars(select(QuestionAnswer).filter_by(**args))]

        return answers, 200
