from app.models import User
from flask import request
from flask_babel import _, lazy_gettext as _l
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, ValidationError, Length


# handles follow & unfollow actions
class EmptyForm(FlaskForm):
    submit = SubmitField(_l('Submit'))


# handles the submission of blog posts
class PostForm(FlaskForm):
    post = TextAreaField(
        _l('Say something'),
        validators=[DataRequired(), Length(min=1, max=140)]
    )
    submit = SubmitField(_l('Submit'))


# handles messages between users
class MessageForm(FlaskForm):
    message = TextAreaField(
        _l('Message'),
        validators=[DataRequired(), Length(min=0, max=140)]
    )
    submit = SubmitField(_l('Submit'))


class EditProfileForm(FlaskForm):
    username = StringField(_l('Username'), validators=[DataRequired()])
    about_me = TextAreaField(_l('About me'), validators=[Length(min=0, max=140)])
    submit = SubmitField(_l('Submit'))

    def __init__(self, original_username, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username

    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=self.username.data).first()
            if user is not None:
                raise ValidationError(_('Please use a different username.'))


class SearchForm(FlaskForm):
    def __init__(self, *args, **kwargs):
        # in a post request, flask places form data in request.form by default.
        # in a get request, flask places form data in the query url string, so flask
        # needs to be pointed towards request.args to get the relevant info
        if 'formdata' not in kwargs:
            kwargs['formdata'] = request.args
        # flask has csrf_enabled by default on form submission, so we need to disable
        # for clickable search links to work and to bypass validation on this form
        if 'csrf_enabled' not in kwargs:
            kwargs['csrf_enabled'] = False
        super(SearchForm, self).__init__(*args, **kwargs)

    # no need for submit. form that has text field will submit on keyboard: Enter
    q = StringField(_l('Search'), validators=[DataRequired()])
