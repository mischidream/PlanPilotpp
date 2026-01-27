from flask import Flask
from flask_cors import CORS
from .persistence.db import db
from .persistence import models
from .rest.fastdownward import fastdownward_bp
from .rest.planpilot import planpilot_bp
from .rest.plannerTest import planner_bp


def configure_extensions(app: Flask):
    """Initialize extension CORS."""
    CORS(app)


def configure_blueprints(app: Flask):
    """Register API blueprints."""
    app.register_blueprint(fastdownward_bp, url_prefix="/api")
    app.register_blueprint(planpilot_bp, url_prefix="/api")
    app.register_blueprint(planner_bp, url_prefix="/api")


def configure_database(app: Flask):
    """Set up database configuration and schema."""
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///mydatabase.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    with app.app_context():
        db.drop_all()
        db.create_all()

        # Uncomment for dev-only full reset:
        # db.session.query(models.FastDownwardRequest).delete()
        # db.session.commit()


def create_app() -> Flask:
    app = Flask(__name__)

    configure_extensions(app)
    configure_blueprints(app)
    configure_database(app)

    return app
