from wtforms import SubmitField, HiddenField
from wtforms.fields import FloatField, TextAreaField
from wtforms.validators import DataRequired, NumberRange

from ._ext import BasePrefixedForm


class GradeAnswerRecordForm(BasePrefixedForm):
    id = HiddenField("ID")
    points = FloatField("Points", validators=[NumberRange(0, 1, "Amount of points should be between 0 and 1")])

    save = SubmitField("Save")


class DeleteAnswerRecordForm(BasePrefixedForm):
    id = HiddenField("ID")
    delete = SubmitField("Delete")
