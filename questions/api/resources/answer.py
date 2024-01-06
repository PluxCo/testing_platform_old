import datetime
import logging

from flask_restful import Resource, reqparse
from sqlalchemy import select, desc, func, update

from api.utils import abort_if_doesnt_exist, view_parser
from models import db_session
from models.db_session import create_session
from models.questions import AnswerRecord, AnswerState, QuestionType

# Request parser for filtering answer resources based on person_id and question_id
fields_parser = view_parser.copy()
fields_parser.add_argument('answer', type=dict, required=False, default={})

planned_answer_parser = reqparse.RequestParser()
planned_answer_parser.add_argument('person_id', type=str, required=True)
planned_answer_parser.add_argument('question_id', type=int, required=True)
planned_answer_parser.add_argument('ask_time', type=datetime.datetime.fromisoformat, required=True)

update_answer_parser = reqparse.RequestParser()
update_answer_parser.add_argument('points', type=float, required=False)
update_answer_parser.add_argument('state', type=AnswerState, required=False)


class AnswerResource(Resource):
    """
    Resource for handling individual AnswerRecord instances.
    """

    @abort_if_doesnt_exist("answer_id", AnswerRecord)
    def get(self, answer_id):
        """
        Get the details of a specific AnswerRecord.

        Args:
            answer_id (int): The ID of the AnswerRecord.

        Returns:
            tuple: A tuple containing the details of the AnswerRecord and HTTP status code.
        """
        with create_session() as db:
            # Retrieve the AnswerRecord from the database and convert it to a dictionary
            db_answer = db.get(AnswerRecord, answer_id).to_dict(rules=("-question",))
        return db_answer, 200

    @abort_if_doesnt_exist("answer_id", AnswerRecord)
    def delete(self, answer_id):
        with create_session() as db:
            answer = db.get(AnswerRecord, answer_id)
            db.delete(answer)
            db.commit()
        return '', 200

    @abort_if_doesnt_exist("answer_id", AnswerRecord)
    def patch(self, answer_id):
        args = {k: v for k, v in update_answer_parser.parse_args().items() if v is not None}

        with create_session() as db:
            db.execute(update(AnswerRecord).where(AnswerRecord.id == answer_id)
                       .values(**args))
            db.commit()

            db_answer = db.get(AnswerRecord, answer_id).to_dict(rules=("-question",))
        return db_answer, 200


class AnswerListResource(Resource):
    """
    Resource for handling lists of AnswerRecord instances.
    """

    def get(self):
        """
        Get a list of AnswerRecord instances based on optional filtering parameters.

        Returns:
            tuple: A tuple containing the list of AnswerRecord instances and HTTP status code.
        """
        # Parse the filtering parameters from the request
        args = fields_parser.parse_args()

        # TODO: add adequate parsers
        answer_filters = args["answer"]
        if "state" in answer_filters:
            answer_filters["state"] = AnswerState(answer_filters["state"])

        question_filters = answer_filters.pop("question", {})
        if "type" in question_filters:
            question_filters["type"] = QuestionType(question_filters["type"])

        with create_session() as db:
            # Retrieve AnswerRecord instances from the database based on the filtering parameters
            db_req = (select(AnswerRecord, func.count(AnswerRecord.id).over())
                      .filter_by(**answer_filters))

            if question_filters:
                db_req = db_req.join(AnswerRecord.question).filter_by(**question_filters)

            db_req = (db_req.order_by(args["orderBy"] if args["order"] == "asc" else desc(args["orderBy"]))
                      .limit(args["resultsCount"])
                      .offset(args["offset"]))

            answers = []
            results_total = 0
            for a, results_total in db.execute(db_req):
                answers.append(a.to_dict(rules=("-question",)))

        return {"results_total": results_total, "results_count": len(answers), "answers": answers}, 200

    def post(self):
        with db_session.create_session() as db:
            args = planned_answer_parser.parse_args()

            new_answer = AnswerRecord(person_id=args['person_id'],
                                      question_id=args['question_id'],
                                      ask_time=args['ask_time'],
                                      state=AnswerState.NOT_ANSWERED)

            db.add(new_answer)
            db.commit()

        return '', 200
