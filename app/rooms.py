from flask import current_app, request
from flask_socketio import emit, join_room

from .utilities import Room, Participant, new_code
from . import socketio


# ------------ In-memory state (RAM only) ------------
ROOMS: dict[str, Room] = {}
SID_TO_ROOM: dict[str, Room] = {}


# ------------ Socket events ------------
@socketio.on("create_room")
def on_create_room(data) -> None:
    # Enforces single room membership
    if SID_TO_ROOM.get(request.sid):
        return emit("error", {"message": "Already in a room"})
    
    name = (data.get("name") or "").strip()
    if not name:
        return emit("error", {"message": "Name required"})

    host = Participant(sid=request.sid, name=name)

    rid = new_code(current_app.config["ROOM_ID_LENGTH"])
    room = Room(host=host)

    ROOMS[rid] = room
    SID_TO_ROOM[request.sid] = room

    join_room(rid)
    emit(
        "room_created",
        {
            "room_id": rid,
            "participants": [p.name for p in room.participants],
            "host_name": host.name,
        },
        to=rid,
    )


@socketio.on("join_room")
def on_join_room(data) -> None:
    rid = (data.get("room_id") or "").strip()
    if not rid:
        return emit("error", {"message": "Room ID required"})
    if rid not in ROOMS:
        return emit("error", {"message": "Room not found"})
    
    # Enforces single room membership
    if SID_TO_ROOM.get(request.sid):
        return emit("error", {"message": "Already in a room"})

    room = ROOMS[rid]

    name = (data.get("name") or "").strip()
    if not name:
        return emit("error", {"message": "Name required"})
    if name in [p.name for p in room.participants]:
        return emit("error", {"message": "Name already taken"})

    participant = Participant(sid=request.sid, name=name)
    room.add_member(participant)

    SID_TO_ROOM[request.sid] = room

    join_room(rid)
    emit("joined", {"name": name}, to=rid)
    _broadcast_room_update(rid)


# ------------ Helpers ------------
def _broadcast_room_update(rid: str) -> None:
    room = ROOMS[rid]
    socketio.emit(
        "room_update",
        {
            "room_id": rid,
            "participants": [p.name for p in room.participants],
            "host_name": room.host.name,
        },
        to=rid,
    )
