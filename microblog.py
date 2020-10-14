from app import create_app, db, cli, login, mail, moment
from app.models import User, Post


app = create_app()
cli.register(app)


@app.shell_context_processor
def make_shell_context():
    '''
    decorator that gives access to the flask env context by
    running 'flask shell' from inside the venv command line
    '''
    return {'db': db, 'User': User, 'Post': Post,
            'login': login, 'mail': mail, 'moment': moment}
