from app import db
from app.errors import bp
from app.api.errors import error_response as api_error_response
from flask import render_template, request


# will use content negotiation btwn client and server to determine response type
def wants_json_response():
    return (request.accept_mimetypes['application/json'] >=
            request.accept_mimetypes['text/html'])


# same as @app.errorhandler(404) but trying to
# make blueprint independent of app for portability
@bp.app_errorhandler(404)
def not_found_error(error):
    if wants_json_response():
        return api_error_response(404)
    return render_template('errors/404.pug'), 404


@bp.app_errorhandler(500)
def internal_error(error):
    db.session.rollback()
    if wants_json_response():
        return api_error_response(500)
    return render_template('errors/500.pug'), 500
