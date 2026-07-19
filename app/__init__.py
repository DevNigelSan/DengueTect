from flask import Flask, render_template

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'denguesense-dev-key-2024'

    from .routes import main
    app.register_blueprint(main)

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404

    from app.ml.auth import init_default_users
    init_default_users()

    return app

