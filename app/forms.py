from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectMultipleField
from wtforms.validators import URL, ValidationError


# noinspection PyUnusedLocal
def url_is_webcal(form, field):
    if not field.data.startswith('webcal://'):
        raise ValidationError('URL must start with webcal://')


class GetCalendarForm(FlaskForm):
    url = StringField('Webcal URL', [URL(), url_is_webcal])
    submit = SubmitField('Continue')


class CustomizeForm(FlaskForm):
    seasons = SelectMultipleField('Seasons')
    groups = SelectMultipleField('Groups')
    submit = SubmitField('Continue')
