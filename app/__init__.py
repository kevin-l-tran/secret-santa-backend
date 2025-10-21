from flask import Flask, current_app
from flask_cors import CORS
from flask_socketio import SocketIO
from dotenv import load_dotenv

socketio: SocketIO
load_dotenv()


def create_app(config_object="config.DevelopmentConfig") -> Flask:
    app: Flask = Flask(__name__)
    app.config.from_object(config_object)

    with app.app_context():
        CORS(app, origins=[current_app.config["FRONTEND_URL"]])

        socketio = SocketIO(cors_allowed_origins=current_app.config["FRONTEND_URL"])
        socketio.init_app(app)

    return app
