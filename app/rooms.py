from flask import current_app, request
from flask_socketio import emit

from .utilities import Room, Participant, new_code
from . import socketio


# ------------ In-memory state (RAM only) ------------
ROOMS: dict[str, Room] = {}


# ------------ Socket events ------------
@socketio.on("create_room")
def create_room(data) -> None:
    name = (data.get("name") or "").strip()
    if not name:
        return emit("error", {"message": "Name required"})

    host = Participant(sid=request.sid, name=name)

    room_id = new_code(current_app.config["ROOM_ID_LENGTH"])
    room = Room(id=room_id, host=host)

    ROOMS[room_id] = room

    emit(
        "room_created",
        {
            "room_id": room.id,
            "participants": [p.name for p in room.participants],
            "host_name": host.name,
        },
    )


@socketio.on("join_room")
def join_room(data) -> None:
    rid = (data.get("room_id") or "").strip()
    if not rid:
        return emit("error", {"message": "Room ID required"})
    if rid not in ROOMS:
        return emit("error", {"message": "Room not found"})

    room = ROOMS[rid]

    name = (data.get("name") or "").strip()
    if not name:
        return emit("error", {"message": "Name required"})
    if name in [p.name for p in room.participants]:
        return emit("error", {"message": "Name already taken"})

    participant = Participant(sid=request.sid, name=name)
    room.add_member(participant)

    emit("joined", {"name": name})
    _broadcast_room_update(room.id)


# ------------ Helpers ------------
def _broadcast_room_update(rid: str) -> None:
    room = ROOMS[rid]
    socketio.emit(
        "room_update",
        {
            "room_id": room.id,
            "participants": [p.name for p in room.participants],
            "host_name": room.host.name,
        },
    )
