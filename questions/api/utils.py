from flask_restful import abort, reqparse

from models.db_session import create_session

view_parser = reqparse.RequestParser()
view_parser.add_argument('order', type=str, required=False, choices=("asc", "desc"), default="asc", location="args")
view_parser.add_argument('orderBy', type=str, required=False, default="id", location="args")
view_parser.add_argument('resultsCount', type=int, required=False, default=-1, location="args")
view_parser.add_argument('offset', type=int, required=False, default=0, location="args")


def abort_if_doesnt_exist(field_name, model):
    """
    Decorator function to abort the request with a 404 error if the specified field value doesn't exist in the database.

    Args:
        field_name (str): The name of the field to check.
        model: The SQLAlchemy model class.

    Returns:
        callable: Decorated function.
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            with create_session() as db:
                # Check if the specified field value exists in the database
                if db.get(model, kwargs[field_name]) is None:
                    abort(404,
                          message=f"The {field_name} with value: {kwargs[field_name]} doesn't exist in the database.")
            return func(*args, **kwargs)

        return wrapper

    return decorator
