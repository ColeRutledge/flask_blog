from app import mail, app
from flask import render_template
from flask_mail import Message
from threading import Thread


def send_async_email(app, msg):
    '''
    context manager for the asynchronous background thread
    :param app: flask app object
    :param msg: email Message object to be sent
    :return:
    '''
    with app.app_context():
        mail.send(msg)


def send_email(subject, sender, recipients, text_body, html_body):
    '''
    handles creating the Message and Thread objects for the reset password emails
    :param subject: subject of the email
    :param sender: from whom the email will be sent
    :param recipients: to whom the email will be sent
    :param text_body: text body of the email
    :param html_body: html body of the email
    :return:
    '''

    msg = Message(
        subject=subject,
        sender=sender,
        recipients=recipients,
        body=text_body,
        html=html_body,
    )
    Thread(target=send_async_email, args=(app, msg)).start()


def send_password_reset_email(user):
    '''
    uses flask_mail to build and send password reset emails
    :param user: user object requesting password reset
    :return:
    '''
    token = user.get_reset_password_token()
    send_email(
        '[Microblog] Reset Your Password',
        sender=app.config['ADMINS'][0],
        recipients=[user.email],
        text_body=render_template('email/reset_password.txt', user=user, token=token),
        html_body=render_template('email/reset_password.pug', user=user, token=token),
    )
