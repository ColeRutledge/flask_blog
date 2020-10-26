from app.api.errors import error_response
from app.models import User
from flask_httpauth import HTTPBasicAuth, HTTPTokenAuth


# protecting routes where client sends user
# credentials in standard auth http header
basic_auth = HTTPBasicAuth()


# need to register two functions with flask-httpauth through
# decorators. will be auto-called for auth as needed by extension
@basic_auth.verify_password
def verify_password(username, password):
    user = User.query.filter_by(username=username).first()
    if user and user.check_password(password):
        return user


@basic_auth.error_handler
def basic_auth_error(status):
    return error_response(status)


# protecting api routes with tokens using flask-httpauth
token_auth = HTTPTokenAuth()


# flask-httpauth will user verify_token
# decorated func when using token auth
@token_auth.verify_token
def verify_token(token):
    return User.check_token(token) if token else None


@token_auth.error_handler
def token_auth_error(status):
    return error_response(status)
