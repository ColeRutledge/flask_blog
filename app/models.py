from app import db, login
from app.search import add_to_index, remove_from_index, query_index
import base64
from datetime import datetime, timedelta
from flask import current_app, url_for
from flask_login import UserMixin
from hashlib import md5
import json
import jwt
import os
import redis
import rq
from time import time
from werkzeug.security import generate_password_hash, check_password_hash


# creates a self-referential many-to-many relationship to link
# instances of the same class -> 'User' no need to declare
# as model bc it is an auxiliary table and has no other use
followers = db.Table(
    'followers',
    db.Column('follower_id', db.Integer, db.ForeignKey('users.id')),
    db.Column('followed_id', db.Integer, db.ForeignKey('users.id')),
)


class PaginatedAPIMixin(object):
    @staticmethod
    def to_collection_dict(query, page, per_page, endpoint, **kwargs):
        resources = query.paginate(page, per_page, False)
        data = {
            'items': [item.to_dict() for item in resources.items],
            'meta': {
                'page': page,
                'per_page': per_page,
                'total_pages': resources.pages,
                'total_items': resources.total,
            },
            'links': {
                'self': url_for(
                            endpoint, page=page,
                            per_page=per_page, **kwargs
                        ),
                'next': url_for(
                            endpoint, page=page + 1,
                            per_page=per_page, **kwargs
                        ) if resources.has_next else None,
                'prev': url_for(
                            endpoint, page=page - 1,
                            per_page=per_page, **kwargs
                        ) if resources.has_prev else None,
            }
        }
        return data


class User(PaginatedAPIMixin, UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    about_me = db.Column(db.String(140))
    token = db.Column(db.String(32), index=True, unique=True)
    token_expiration = db.Column(db.DateTime)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    last_message_read_time = db.Column(db.DateTime)
    created_on = db.Column(db.DateTime, server_default=db.func.now())
    updated_on = db.Column(
        db.DateTime,
        server_default=db.func.now(),
        server_onupdate=db.func.now()
    )
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    notifications = db.relationship('Notification', backref='user', lazy='dynamic')
    tasks = db.relationship('Task', backref='user', lazy='dynamic')
    followed = db.relationship(
        'User',
        secondary=followers, lazy='dynamic',
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        backref=db.backref('followers', lazy='dynamic'),
    )
    messages_sent = db.relationship(
        'Message',
        backref='author', lazy='dynamic',
        foreign_keys='Message.sender_id',
    )
    messages_received = db.relationship(
        'Message',
        backref='recipient', lazy='dynamic',
        foreign_keys='Message.recipient_id',
    )

    def __repr__(self):
        return f'<User {self.username}>'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_token(self, expires_in=3600):
        now = datetime.utcnow()
        if self.token and self.token_expiration > now + timedelta(seconds=60):
            return self.token
        self.token = base64.b64encode(os.urandom(24)).decode('utf-8')
        self.token_expiration = now + timedelta(seconds=expires_in)
        db.session.add(self)
        return self.token

    def revoke_token(self):
        self.token_expiration = datetime.utcnow() - timedelta(seconds=1)

    @staticmethod
    def check_token(token):
        user = User.query.filter_by(token=token).first()
        if user is None or user.token_expiration < datetime.utcnow():
            return None
        return User

    def to_dict(self, include_email=False):
        data = {
            'id': self.id,
            'username': self.username,
            'last_seen': self.last_seen.isoformat() + 'Z',
            'about_me': self.about_me,
            'post_count': self.posts.count(),
            'follower_count': self.followers.count(),
            'followed_count': self.followed.count(),
            '_links': {
                'self': url_for('api.get_user', id=self.id),
                'followers': url_for('api.get_followers', id=self.id),
                'followed': url_for('api.get_followed', id=self.id),
                'avatar': self.avatar(128),
            }
        }
        if include_email:
            data['email'] = self.email
        return data

    def from_dict(self, data, new_user=False):
        for field in ['username', 'email', 'about_me']:
            if field in data:
                setattr(self, field, data[field])
            if new_user and 'password' in data:
                self.set_password(data['password'])

    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return f'https://www.gravatar.com/avatar/{digest}?d=identicon&s={size}'

    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)

    def is_following(self, user):
        return self.followed.filter(
            followers.c.followed_id == user.id).count() > 0

    def followed_posts(self):
        followed = (Post.query
                        .join(followers, followers.c.followed_id == Post.user_id)
                        .filter(followers.c.follower_id == self.id))
        own = Post.query.filter_by(user_id=self.id)
        return followed.union(own).order_by(Post.timestamp.desc())

    def get_reset_password_token(self, expires_in=600):
        return (jwt.encode({'reset_password': self.id, 'exp': time() + expires_in},
                           current_app.config['SECRET_KEY'],
                           algorithm='HS256')
                   .decode('utf-8'))

    def new_messages(self):
        last_read_time = self.last_message_read_time or datetime(1900, 1, 1)
        return (Message.query.filter_by(recipient=self)
                             .filter(Message.timestamp > last_read_time)
                             .count())

    def add_notification(self, name, data):
        self.notifications.filter_by(name=name).delete()
        n = Notification(name=name, payload_json=json.dumps(data), user=self)
        db.session.add(n)
        return n

    def launch_task(self, name, description, *args, **kwargs):
        rq_job = current_app.task_queue.enqueue('app.tasks.' + name, self.id, *args, **kwargs)
        task = Task(id=rq_job.get_id(), name=name, description=description, user=self)
        db.session.add(task)
        return task

    def get_tasks_in_progress(self):
        return Task.query.filter_by(user=self, complete=False).all()

    def get_task_in_progress(self, name):
        return Task.query.filter_by(name=name, user=self, complete=False).first()

    @login.user_loader
    def load_user(id):
        return User.query.get(int(id))

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token,
                            current_app.config['SECRET_KEY'],
                            algorithms=['HS256'])['reset_password']
        except: # noqa
            return
        return User.query.get(id)


class SearchableMixin(object):
    @classmethod
    def search(cls, expression, page, per_page):
        '''
        class method: wraps the query_index method from app.search. uses the results
        to query the rdb. provides a way to connect model objects with the indexes in
        elastic and keeps them in sync by using sqlalchemy events to listen for changes.

        :param cls:         'class' -> refers to the model invoking this method. (e.g. - Post)
        :param expression:  the search query
        :param page:        refers to page number. used for returning the correct results based
                            on pagination
        :param per_page:    results per page to allow calculation for proper pagination results
        :returns:           tuple -> (lst(Post.id), int(num_results))
                            if no results found, will return empty db object and 0,
                            otherwise, will return a list of ids and the number of results
        '''
        ids, total = query_index(cls.__tablename__, expression, page, per_page)
        if total == 0:
            return cls.query.filter_by(id=0), 0
        when = []
        for i in range(len(ids)):
            when.append((ids[i], i))
        return cls.query.filter(cls.id.in_(ids)).order_by(db.case(when, value=cls.id)), total

    @classmethod
    def before_commit(cls, session):
        '''
        class method: sqlalchemy event will trigger this before all session commits. method will
        identify objects in the session that need to be indexed in elastic search and copy them
        into the _changes property on the session which allows for easy reaccess following commit.

        :param cls:         'class' -> refers to the model invoking this method (e.g. - Post)
        :param session:     the database session object
        :returns:
        '''
        session._changes = {
            'add': list(session.new),
            'update': list(session.dirty),
            'delete': list(session.deleted),
        }

    @classmethod
    def after_commit(cls, session):
        '''
        class method: wraps the add_to_index method from app.search. sqlalchemy event will trigger
        this after all session commits. method will loop over all session objects and add them
        to an index in elastic search before resetting the session._changes property.

        :param cls:         'class' -> refers to the model invoking this method. (e.g. - Post)
        :param session:     the database session object
        :returns:
        '''
        for obj in session._changes['add']:
            if isinstance(obj, SearchableMixin):
                add_to_index(obj.__tablename__, obj)
        for obj in session._changes['update']:
            if isinstance(obj, SearchableMixin):
                add_to_index(obj.__tablename__, obj)
        for obj in session._changes['delete']:
            if isinstance(obj, SearchableMixin):
                remove_from_index(obj.__tablename__, obj)
        session._changes = None

    @classmethod
    def reindex(cls):
        '''
        class method: wraps the add_to_index method from app.search. will reindex any
        model fields marked for indexing in the sqlalchemy models. provides a way to
        reset the elastic search indexes.

        :param cls:         'class' -> refers to the model invoking this method. (e.g. - Post)
        :returns:
        '''
        for obj in cls.query:
            add_to_index(cls.__tablename__, obj)


class Post(SearchableMixin, db.Model):
    __tablename__ = 'posts'
    __searchable__ = ['body']

    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(140))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    language = db.Column(db.String(5))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    updated_on = db.Column(
        db.DateTime,
        server_default=db.func.now(),
        server_onupdate=db.func.now()
    )

    def __repr__(self):
        return f'<Post {self.body}>'


class Message(db.Model):
    __tablename__ = 'messages'

    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    recipient_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    body = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    def __repr__(self):
        return f'<Message {self.body}>'


class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    timestamp = db.Column(db.Float, index=True, default=time)
    payload_json = db.Column(db.Text)

    def get_data(self):
        return json.loads(str(self.payload_json))


class Task(db.Model):
    __tablename__ = 'tasks'

    # id is string instead of integer for managing index in redis
    id = db.Column(db.String(36), primary_key=True)
    name = db.Column(db.String(128), index=True)
    description = db.Column(db.String(128))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    complete = db.Column(db.Boolean, default=False)

    def get_rq_job(self):
        ''' returns the redis queue job instance for the given task '''
        try:
            rq_job = rq.job.Job.fetch(self.id, connection=current_app.redis)
        except (redis.exceptions.RedisError, rq.exceptions.NoSuchJobError):
            return None
        return rq_job

    def get_progress(self):
        '''
        if job id from model does not exist in rq, job has finished and will
        return 100. if job exists but no 'meta' attribute, job is scheduled to
        run so will return 0 as progress.

        :param self:        Task
        :returns:           float -> the updated % progress of a given task
        '''
        job = self.get_rq_job()
        return job.meta.get('progress', 0) if job is not None else 100


db.event.listen(db.session, 'before_commit', SearchableMixin.before_commit)
db.event.listen(db.session, 'after_commit', SearchableMixin.after_commit)
