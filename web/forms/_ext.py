from flask_wtf import FlaskForm
from flask_wtf.form import _Auto


class BasePrefixedForm(FlaskForm):
    def __init__(self, formdata=_Auto, **kwargs):
        if "prefix" not in kwargs:
            super().__init__(formdata, prefix=type(self).__name__.lower(), **kwargs)
        else:
            super().__init__(formdata, **kwargs)
