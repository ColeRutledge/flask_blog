from app import mail
from flask import current_app
from flask_mail import Message
from threading import Thread


def send_async_email(app, msg):
    '''
    context manager for the asynchronous background thread

    :param app:             flask app object
    :param msg:             email Message object to be sent
    :return:
    '''
    with app.app_context():
        mail.send(msg)


def send_email(subject, sender, recipients, text_body,
               html_body, attachments=None, sync=False):
    '''
    handles creating the Message and Thread objects for app emails.
    will send synchronously by default and async with sync=True.

    :param subject:         subject of the email
    :param sender:          from whom the email will be sent
    :param recipients:      to whom the email will be sent
    :param text_body:       text body of the email
    :param html_body:       html body of the email
    :param attachments:
    :return:
    '''
    msg = Message(
        subject=subject,
        sender=sender,
        recipients=recipients,
        body=text_body,
        html=html_body,
    )
    if attachments:
        for attachment in attachments:
            # attach method of the message class accepts three
            # args: filename, media type, and actual file data
            msg.attach(*attachment)
    if sync:
        mail.send(msg)
    else:
        Thread(target=send_async_email,
               args=(current_app._get_current_object(), msg)).start()
