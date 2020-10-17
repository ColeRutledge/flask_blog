from app import db, login
from app.search import add_to_index, remove_from_index, query_index
from datetime import datetime
from flask import current_app
from flask_login import UserMixin
from hashlib import md5
import jwt
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


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    about_me = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    created_on = db.Column(db.DateTime, server_default=db.func.now())
    updated_on = db.Column(
        db.DateTime,
        server_default=db.func.now(),
        server_onupdate=db.func.now()
    )

    posts = db.relationship('Post', backref='author', lazy='dynamic')
    followed = db.relationship(
        'User', secondary=followers, lazy='dynamic',
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        backref=db.backref('followers', lazy='dynamic'),
    )

    def __repr__(self):
        return f'<User {self.username}>'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

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


db.event.listen(db.session, 'before_commit', SearchableMixin.before_commit)
db.event.listen(db.session, 'after_commit', SearchableMixin.after_commit)
