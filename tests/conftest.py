import pytest

from app import create_app, socketio
import app.rooms as rooms


@pytest.fixture
def app():
    app = create_app("config.DevelopmentConfig")
    ctx = app.app_context()
    ctx.push()
    yield app
    ctx.pop()


@pytest.fixture
def sio(app):
    """Flask-SocketIO test client bound to the app."""
    return socketio.test_client(app, flask_test_client=app.test_client())


@pytest.fixture(autouse=True)
def reset_rooms():
    """Clear in-memory state between tests."""
    rooms.ROOMS.clear()
    yield
    rooms.ROOMS.clear()
