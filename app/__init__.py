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

    # Initialize database and default users on startup
    from app.ml.database import init_db
    from app.ml.auth import init_default_users
    init_db()
    init_default_users()

    return app