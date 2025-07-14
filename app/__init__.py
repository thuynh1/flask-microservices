import os

from dotenv import load_dotenv
from flask import Flask
from app.apis.routes import items_bp
from app.extensions import db

def create_app(configs: dict = None) -> Flask:
    app = Flask(__name__)

    # Configuration
    if configs:
        app.config.update(configs)
    else:
        # todo - use pydantic-settings
        load_dotenv()
        app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URI")

    # Initialize extensions
    db.init_app(app)

    # Register blueprints
    app.register_blueprint(items_bp)

    # todo - Register error handlers

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)