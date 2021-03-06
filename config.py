from pathlib import Path
import os


basedir = Path().cwd()
# basedir = Path().absolute()
# basedir = Path(__file__).parent.resolve()


class Config(object):
    LANGUAGES = ['en', 'es']
    POSTS_PER_PAGE = 15
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://'
    REDISTOGO_URL = os.environ.get('REDISTOGO_URL') or REDIS_URL
    ELASTICSEARCH_URL = os.environ.get('ELASTICSEARCH_URL')
    MS_TRANSLATOR_KEY = os.environ.get('MS_TRANSLATOR_KEY')
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    ADMINS = os.environ.get('ADMINS', '').split(',')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + str(basedir.joinpath('app.db'))
        # 'sqllite:///' + basedir.joinpath('app.db').as_posix() # noqa
