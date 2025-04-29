from flask import Flask

def create_app():
    app = Flask(__name__)

    # Register Blueprints for API endpoints
    from .rest.fastdownward import fastdownward_bp
    app.register_blueprint(fastdownward_bp, url_prefix='/api')

    return app
