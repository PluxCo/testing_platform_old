from wtforms import SubmitField, HiddenField, BooleanField
from wtforms.fields import StringField, DateTimeField, IntegerField, TextAreaField, SelectMultipleField
from wtforms.validators import DataRequired, ValidationError

from ._ext import BasePrefixedForm


class CustomAnswerValidator(object):
    def __init__(self, message=None):
        if not message:
            message = "Invalid answer format"
        self.message = message

    def __call__(self, form, field):
        is_open = form.is_open.data
        answer_value = field.data

        if is_open:
            # If 'is_open' is True, the answer should be text
            if not isinstance(answer_value, str):
                raise ValidationError(self.message)
        else:
            # If 'is_open' is False, the answer should be a number between 1 and the number of options
            try:
                answer_index = int(answer_value)
                options_count = len(form.options.data.split('\n'))
                if not (1 <= answer_index <= options_count):
                    raise ValidationError(self.message)
            except ValueError:
                raise ValidationError(self.message)


class CreateQuestionForm(BasePrefixedForm):
    text = TextAreaField("Text", validators=[DataRequired()])
    subject = StringField("Subject")
    options = TextAreaField("Options (one per line)")
    answer = TextAreaField("Answer index", validators=[CustomAnswerValidator()])
    groups = SelectMultipleField("Groups")
    level = IntegerField("Difficulty", default=1)
    article = StringField("Article")
    is_open = BooleanField("Question with open answer")

    create = SubmitField("Create")


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
