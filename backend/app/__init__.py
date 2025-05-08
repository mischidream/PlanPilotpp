from flask import Flask
from flask_cors import CORS
from .persistence.db import db
from .persistence import models
from .rest.fastdownward import fastdownward_bp
from .rest.planpilot import planpilot_bp

def create_app():
    app = Flask(__name__)

    CORS(app)

    # Register Blueprints for API endpoints
    app.register_blueprint(fastdownward_bp, url_prefix='/api')
    app.register_blueprint(planpilot_bp, url_prefix='/api')

    # Initialize database
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mydatabase.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    with app.app_context():
        db.create_all()

        # Delete all entries
        #db.session.query(models.FastDownwardRequest).delete()
        #db.session.commit()

    return app
