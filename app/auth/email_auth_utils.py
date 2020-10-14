from app.email_utils import send_email
from flask import render_template, current_app
from flask_babel import _


def send_password_reset_email(user):
    '''
    uses flask_mail to build and send password reset emails
    :param user: user object requesting password reset
    :return:
    '''
    token = user.get_reset_password_token()
    send_email(
        _('[Microblog] Reset Your Password'),
        sender=current_app.config['ADMINS'][0],
        recipients=[user.email],
        text_body=render_template('email/reset_password.txt', user=user, token=token),
        html_body=render_template('email/reset_password.pug', user=user, token=token),
    )
