from config import Config
from datetime import datetime
from flask import (
    flash, Flask, redirect,
    render_template, request, url_for,
)
from flask_babel import Babel, _, lazy_gettext as _l
from flask_bootstrap import Bootstrap
from flask_login import (
    current_user, LoginManager, login_required,
    login_user, logout_user,
)
from flask_mail import Mail
from flask_migrate import Migrate
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from logging.handlers import SMTPHandler, RotatingFileHandler
import logging
import re
# import redis
import os
# import time
from werkzeug.urls import url_parse


app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
babel = Babel(app)
mail = Mail(app)
moment = Moment(app)
login = LoginManager(app)
login.login_view = 'login'
login.login_message = _l('Please log in to access this page.')
bootstrap = Bootstrap(app)
app.jinja_env.add_extension('pypugjs.ext.jinja.PyPugJSExtension')
# cache = redis.Redis(host='redis_cache', port=6379, decode_responses=True)

from forms import (
    LoginForm, RegistrationForm, EditProfileForm,
    EmptyForm, PostForm, ResetPasswordRequestForm, ResetPasswordForm
)
from models import User, Post
from email_utils import send_password_reset_email
import errors


# configures logs and email notifications on server issues in production
# if not app.debug:

# EMAIL NOTIFICATIONS
if app.config['MAIL_SERVER']:

    auth = None
    if app.config['MAIL_USERNAME'] or app.config['MAIL_PASSWORD']:
        auth = (app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])

    secure = None
    if app.config['MAIL_USE_TLS']:
        secure = ()

    mail_handler = SMTPHandler(
        mailhost=(app.config['MAIL_SERVER'], app.config['MAIL_PORT']),
        fromaddr='no-reply@' + app.config['MAIL_SERVER'],
        toaddrs=app.config['ADMINS'], subject='Microblog Failure',
        credentials=auth, secure=secure,
    )
    mail_handler.setLevel(logging.ERROR)
    app.logger.addHandler(mail_handler)

# LOGS -- INDENT TO USE FOR PROD ONLY
if not os.path.exists('logs'):
    os.mkdir('logs')
file_handler = RotatingFileHandler(
    'logs/microblog.log',
    maxBytes=10240,
    backupCount=10,
)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
file_handler.setLevel(logging.INFO)
app.logger.addHandler(file_handler)

app.logger.setLevel(logging.INFO)
app.logger.info('Microblog startup')


@app.shell_context_processor
def make_shell_context():
    '''
    decorator that gives access to the flask env context by
    running 'flask shell' from inside the venv command line
    '''
    return {'db': db, 'User': User, 'Post': Post,
            'login': login, 'mail': mail, 'moment': moment}


@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()


@babel.localeselector
def get_locale():
    return request.accept_languages.best_match(app.config['LANGUAGES'])
    # return 'es'


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(body=form.post.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash(_('Your post is now live!'))
        return redirect(url_for('index'))

    page = request.args.get('page', 1, type=int)
    posts = (
        current_user.followed_posts()
                    .paginate(
                        page=page, error_out=False,
                        per_page=app.config['POSTS_PER_PAGE'],
                    )
    )
    next_url = url_for('index', page=posts.next_num) if posts.has_next else None
    prev_url = url_for('index', page=posts.prev_num) if posts.has_prev else None
    return render_template(
        'index.pug',
        title=_('Home Page'), form=form, posts=posts.items,
        next_url=next_url, prev_url=prev_url,
    )


@app.route('/explore')
@login_required
def explore():
    page = request.args.get('page', 1, type=int)
    posts = (
        Post.query.order_by(Post.timestamp.desc())
                  .paginate(
                      page=page, error_out=False,
                      per_page=app.config['POSTS_PER_PAGE'],
                  )
    )
    next_url = url_for('explore', page=posts.next_num) if posts.has_next else None
    prev_url = url_for('explore', page=posts.prev_num) if posts.has_prev else None
    return render_template(
        'index.pug',
        title=_('Explore'), posts=posts.items,
        next_url=next_url, prev_url=prev_url,
    )


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
            flash(_('Invalid username or password'))
            return redirect(url_for('login'))

        # for security only redirect when url is relative
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')

        return redirect(url_for('index'))
    return render_template('login.pug', title=_('Sign In'), form=form)


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
        flash(_('Congratulations, you are now a registered user!'))
        return redirect(url_for('login'))
    return render_template('register.pug', title=_('Register'), form=form)


@app.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    posts = (
        user.posts.order_by(Post.timestamp.desc())
                  .paginate(
                      page=page, error_out=False,
                      per_page=app.config['POSTS_PER_PAGE'],
                  )
    )
    next_url = url_for('user', username=user.username, page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('user', username=user.username, page=posts.prev_num) \
        if posts.has_prev else None
    form = EmptyForm()
    return render_template(
        'user.pug',
        user=user, posts=posts.items, form=form,
        next_url=next_url, prev_url=prev_url,
    )


@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash(_('Your changes have been saved.'))
        return redirect(url_for('edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.pug', title=_('Edit Profile'), form=form)


@app.route('/follow/<username>', methods=['POST'])
@login_required
def follow(username):

    form = EmptyForm()
    if form.validate_on_submit():

        user = User.query.filter_by(username=username).first()
        if user is None:
            flash(_('User %(username)s not found.', username=username))
            return redirect(url_for('index'))
        if user == current_user:
            flash(_('You cannot follow yourself!'))
            return redirect(url_for('user', username=username))

        current_user.follow(user)
        db.session.commit()
        flash(_('You are following %(username)s.', username=username))
        return redirect(url_for('user', username=username))
    else:
        #  CSRF token is missing or invalid
        return redirect(url_for('index'))


@app.route('/unfollow/<username>', methods=['POST'])
@login_required
def unfollow(username):

    form = EmptyForm()
    if form.validate_on_submit():

        user = User.query.filter_by(username=username).first()
        if user is None:
            flash(_('User %(username)s not found.', username=username))
            return redirect(url_for('index'))
        if user == current_user:
            flash(_('You cannot unfollow yourself!'))
            return redirect(url_for('user'), username=username)

        current_user.unfollow(user)
        db.session.commit()
        flash(_('You have unfollowed %(username)s.', username=username))
        return redirect(url_for('user', username=username))
    else:
        # CSRF token is missing or invalid
        return redirect(url_for('index'))


@app.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash(_('Check your email for the instructions to reset your password'))
        return redirect(url_for('login'))

    return render_template(
        'reset_password_request.pug',
        title=_('Reset Password'), form=form
    )


@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('index'))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash(_('Your password has been reset.'))
        return redirect(url_for('login'))

    return render_template('reset_password.pug', form=form)


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
