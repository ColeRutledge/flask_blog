from flask_sqlalchemy import SQLAlchemy
from werkzeug.urls import url_parse
from flask_migrate import Migrate
from datetime import datetime
import re
from flask import (
    Flask,
    render_template,
    flash, redirect,
    url_for,
    request
)
from flask_login import (
    LoginManager,
    current_user,
    login_user,
    logout_user,
    login_required,
)
from config import Config
# import redis
# import time


app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login = LoginManager(app)
login.login_view = 'login'
app.jinja_env.add_extension('pypugjs.ext.jinja.PyPugJSExtension')
# cache = redis.Redis(host='redis_cache', port=6379, decode_responses=True)

from forms import LoginForm, RegistrationForm # noqa
from models import User, Post # noqa


@app.shell_context_processor
def make_shell_context():
    '''
    decorator that gives access to the flask env context by
    running 'flask shell' from inside the venv command line
    '''
    return {'db': db, 'User': User, 'Post': Post}


@app.route('/')
@app.route('/index')
@login_required
def index():
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
    return render_template('index.pug', title='Home Page', posts=posts)


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
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = LoginForm()
    if form.validate_on_submit():

        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))

        # for security only redirect when url is relative
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')

        return redirect(url_for('index'))
    return render_template('login.pug', title='Sign In', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.pug', title='Register', form=form)


@app.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    posts = [
        {'author': user, 'body': 'Test post #1'},
        {'author': user, 'body': 'Test post #2'},
    ]
    return render_template('user.pug', user=user, posts=posts)


# ######### REDIS ######### #

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
