from flask_wtf import FlaskForm
from wtforms import SubmitField, HiddenField
from wtforms.fields import StringField, DateTimeField, IntegerField, TextAreaField, SelectMultipleField
from wtforms.validators import DataRequired, ValidationError

from ._ext import BasePrefixedForm


class CreateQuestionForm(BasePrefixedForm):
    text = TextAreaField("Text", validators=[DataRequired()])
    subject = StringField("Subject")
    options = TextAreaField("Options (one per line)")
    answer = IntegerField("Answer index")
    groups = SelectMultipleField("Groups")
    level = IntegerField("Difficulty", default=1)
    article = StringField("Article")

    create = SubmitField("Create")

    def validate_answer(self, field):
        if field.data < 1 or field.data > len(self.options.data.splitlines()):
            raise ValidationError("Answer index should be from 1 to options count")


class ImportQuestionForm(BasePrefixedForm):
    import_data = TextAreaField("Data", validators=[DataRequired()])
    subject = StringField("Subject")
    groups = SelectMultipleField("Groups")
    article = StringField("Article")

    import_btn = SubmitField("Create")


class PlanQuestionForm(BasePrefixedForm):
    question_id = IntegerField()
    person_id = IntegerField()
    ask_time = DateTimeField("Ask time", format='%d.%m.%Y %H:%M')

    plan = SubmitField("Plan it")


class EditQuestionForm(BasePrefixedForm):
    id = HiddenField("ID")
    text = TextAreaField("Text", validators=[DataRequired()])
    subject = StringField("Subject")
    options = TextAreaField("Options (one per line)")
    answer = IntegerField("Answer index")
    groups = SelectMultipleField("Groups")
    level = IntegerField("Difficulty", default=1)
    article = StringField("Article")

    save = SubmitField("Save")

    def validate_answer(self, field):
        if field.data < 1 or field.data > len(self.options.data.splitlines()):
            raise ValidationError("Answer index should be from 1 to options count")


class DeleteQuestionForm(BasePrefixedForm):
    id = HiddenField("ID")
    delete = SubmitField("Delete")
