import os
from pathlib import Path

basedir = Path().cwd()
# basedir = Path().absolute()
# basedir = Path(__file__).parent.resolve()


class Config(object):
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + str(basedir.joinpath('app.db'))
        # 'sqllite:///' + basedir.joinpath('app.db').as_posix() # noqa
