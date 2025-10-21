from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO

socketio = SocketIO(cors_allowed_origins="*") # later replace with FRONTEND_URL

def create_app():
    app = Flask(__name__)
    
    CORS(app)

    socketio.init_app(app)

    return app