from flask import Flask
from database.database import create_table


def create_app():
    app = Flask(__name__)

    create_table()      # Create table automatically

    from app.routes import main
    app.register_blueprint(main)

    return app