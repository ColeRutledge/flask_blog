from flask import Flask, render_template, flash, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime
import re

from config import Config
from forms import LoginForm
# import redis
# import time


app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
app.jinja_env.add_extension('pypugjs.ext.jinja.PyPugJSExtension')
# cache = redis.Redis(host='redis_cache', port=6379, decode_responses=True)

from models import User, Post # noqa


@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Post': Post}


# def get_hit_count():
#     retries = 5
#     while True:
#         try:
#             return cache.incr('hits')
#         except redis.exceptions.ConnectionError as exc:
#             if retries == 0:
#                 raise exc
#             retries -= 1
#             time.sleep(0.5)


# @app.route('/')
# def hello():
#     count = get_hit_count()
#     return render_template('index.pug')


@app.route('/')
@app.route('/index')
def index():
    user = {'username': 'Cole'}
    posts = [
        {
            'author': {'username': 'John'},
            'body': 'Beautiful day in Portland!'
        },
        {
            'author': {'username': 'Susan'},
            'body': 'The Avengers movie was so cool!'
        },
    ]
    return render_template('index.pug', user=user, title='Home', posts=posts)


@app.route("/hello/<name>")
def hello_there(name):
    now = datetime.now()
    formatted_now = now.strftime("%A, %d %B, %Y at %X")
    # Filter the name argument to letters only using regular expressions. URL
    # arguments can contain arbitrary text, so we restrict to safe characters.
    match_object = re.match("[a-zA-Z]+", name)

    if match_object:
        clean_name = match_object.group()
    else:
        clean_name = "Friend"

    content = "Hello there, " + clean_name + "! It's " + formatted_now
    return content


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        flash(
            f'Login requested for user {form.username.data}, \
            remember_me={form.remember_me.data}'
        )
        return redirect(url_for('index'))
    return render_template('login.pug', title='Sign In', form=form)
