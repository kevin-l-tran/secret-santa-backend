from flask import current_app, request
from flask_socketio import emit

from .utilities import Room, Participant, new_code
from . import socketio


# ------------ In-memory state (RAM only) ------------
ROOMS: dict[str, Room] = {}


# ------------ Socket events ------------
@socketio.on("create_room")
def create_room(data):
    name = (data.get("name") or "").strip()
    if not name:
        return emit("error", {"message": "Name required"})

    host = Participant(sid=request.sid, name=name)

    room_id = new_code(current_app.config["ROOM_ID_LENGTH"])
    room = Room(id=room_id, host=host)

    ROOMS[room_id] = room
    emit("room_created", {
        "room_id": room.id,
        "participants": [p.name for p in room.participants],
        "host_name": host.name,
    })
