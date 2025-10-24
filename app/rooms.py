from flask import current_app, request
from flask_socketio import emit, join_room

from .utilities import Room, Participant, knuth_shuffle, new_code
from . import socketio


# ------------ In-memory state (RAM only) ------------
ROOMS: dict[str, Room] = {}
SID_TO_RID: dict[str, str] = {}


# ------------ Socket events ------------
@socketio.on("create_room")
def on_create_room(data) -> None:
    if SID_TO_RID.get(request.sid):
        return emit("error", {"message": "Already in a room"})

    name = (data.get("name") or "").strip()
    if not name:
        return emit("error", {"message": "Name required"})

    host = Participant(sid=request.sid, name=name)

    rid = new_code(current_app.config["ROOM_ID_LENGTH"])
    room = Room(host=host)

    ROOMS[rid] = room
    SID_TO_RID[request.sid] = rid

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

    if SID_TO_RID.get(request.sid):
        return emit("error", {"message": "Already in a room"})

    room = ROOMS[rid]

    name = (data.get("name") or "").strip()
    if not name:
        return emit("error", {"message": "Name required"})
    if name in [p.name for p in room.participants]:
        return emit("error", {"message": "Name already taken"})

    participant = Participant(sid=request.sid, name=name)
    room.add_member(participant)

    SID_TO_RID[request.sid] = rid

    join_room(rid)
    emit("joined", {"name": name}, to=rid)
    _broadcast_room_update(rid)


@socketio.on("disconnect")
def on_disconnect() -> None:
    sid = request.sid

    rid = SID_TO_RID.get(sid)
    room = ROOMS.get(rid)
    if not room:
        return
    else:
        SID_TO_RID.pop(sid, None)

    participant: Participant | None = None
    for p in room.participants:
        if p.sid == sid:
            participant = p
            break
    if not participant:
        return

    room.participants.remove(participant)
    if participant == room.host:
        if room.participants:
            room.host = room.participants[0]
            emit("host_changed", {"host_name": room.host.name}, to=rid)
        else:
            ROOMS.pop(rid, None)
            return

    emit("disconnected", {"name": participant.name}, to=rid)
    _broadcast_room_update(rid)


@socketio.on("reveal")
def on_reveal() -> None:
    sid = request.sid

    rid = SID_TO_RID.get(sid)
    room = ROOMS.get(rid)
    if not room:
        return emit("error", {"message": "Not in a room"})

    if room.host.sid != sid:
        return emit("error", {"message": "Not the host"})

    participants = room.participants
    if len(participants) < 2:
        return emit("error", {"message": "Not enough participants"})

    giftees = knuth_shuffle(participants.copy())
    for i in range(len(participants)):
        emit("revealed", {"giftee_name": giftees[i].name}, to=participants[i].sid)


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
