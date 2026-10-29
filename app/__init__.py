from flask import Flask, render_template
from datetime import timedelta

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'denguesense-dev-key-2024'
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)   # "Remember me" duration

    from .routes import main
    app.register_blueprint(main)

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return render_template('404.html', code=405, title='That action is not allowed here',
                               desc='This page cannot be used that way. Please go back and try again.'), 405

    @app.errorhandler(500)
    def server_error(e):
        return render_template('404.html', code=500, title='Something went wrong',
                               desc='DengueTect hit an unexpected problem and could not finish this request. '
                                    'Please go back and try again. If it keeps happening, contact the IT Admin.'), 500

    # Initialize database and default users on startup
    from app.ml.database import init_db
    from app.ml.auth import init_default_users
    init_db()
    init_default_users()

    return app