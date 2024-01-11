from wtforms import SubmitField, HiddenField
from wtforms.fields import FloatField, TextAreaField
from wtforms.validators import DataRequired, NumberRange

from ._ext import BasePrefixedForm


class DeleteAnswerRecordForm(BasePrefixedForm):
    id = HiddenField("ID")
    delete = SubmitField("Delete")
