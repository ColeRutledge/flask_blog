from app import db
from app.errors import bp
from flask import render_template


# same as @app.errorhandler(404) but trying to
# make blueprint independent of app for portability
@bp.app_errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.pug'), 404


@bp.app_errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('errors/500.pug'), 500
