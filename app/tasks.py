from app import create_app
from app import db
from app.email_utils import send_email
from app.models import Task, User, Post
from flask import render_template
import json
from rq import get_current_job
import sys
import time


app = create_app()
app.app_context().push()


def _set_task_progress(progress):
    job = get_current_job()
    if job:
        job.meta['progress'] = progress
        job.save_meta()
        task = Task.query.get(job.get_id())
        task.user.add_notification(
            'task_progress',
            {'task_id': job.get_id(), 'progress': progress},
        )
        if progress >= 100:
            task.complete = True
        db.session.commit()


def export_posts(user_id):
    try:
        # read user posts from database
        # send email with data to user
        user = User.query.get(user_id)
        _set_task_progress(0)
        data = []
        i = 0
        total_posts = user.posts.count()
        for post in user.posts.order_by(Post.timestamp.asc()):
            data.append({
                'body': post.body,
                'timestamp': post.timestamp.isoformat() + 'Z'
            })
            time.sleep(5)
            i += 1
            _set_task_progress(100 * i // total_posts)

        send_email(
            '[Microblog] Your blog posts',
            sender=app.config['ADMINS'][0], recipients=[user.email], sync=True,
            text_body=render_template('email/export_posts.txt', user=user),
            html_body=render_template('email/export_posts.pug', user=user),
            attachments=[('posts.json',
                          'application/json',
                          json.dumps({'posts': data}, indent=4))],
        )
    except: # noqa
        # handle unexpected errors
        app.logger.error('Unhandled exception', exc_info=sys.exc_info())
    finally:
        # handle cleanup
        _set_task_progress(100)


# def example(seconds):
#     job = get_current_job()
#     print('Starting task 1')
#     for i in range(seconds):
#         job.meta['progress'] = 100.0 * i / seconds
#         job.save_meta()
#         print(i)
#         time.sleep(1)
#     job.meta['progress'] = 100
#     job.save_meta()
#     print('Task completed')


# def example2(name):
#     print('Starting task 2')
#     for i in range(10):
#         print(i)
#         time.sleep(1)
#     print(f'Hello {name}')
