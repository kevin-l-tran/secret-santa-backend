import app.rooms as rooms


# ------------ Create room tests ------------
def test_create_room_success(sio):
    # Act
    sio.emit("create_room", {"name": "Alice"})
    received = sio.get_received()

    # Assert: event output
    payload = _get_packet(received, "room_created")
    assert payload is not None, f"Got: {received}"
    assert payload["host_name"] == "Alice"
    assert payload["participants"] == ["Alice"]

    # Assert: in-memory state updated
    room = rooms.ROOMS[payload["room_id"]]
    assert len(rooms.ROOMS) == 1
    assert room.host.name == payload["host_name"]
    assert [p.name for p in room.participants] == ["Alice"]

    assert len(rooms.SID_TO_RID) == 1
    assert rooms.SID_TO_RID[room.host.sid] == payload["room_id"]


def test_create_room_without_name(sio):
    # Act
    sio.emit("create_room", {})
    received_no_name = sio.get_received()
    sio.emit("create_room", {"name": " \n \t   "})
    received_whitespace = sio.get_received()

    # Assert: event output
    payload = _get_packet(received_no_name, "error")
    assert payload is not None, f"Got: {received_no_name}"
    assert payload["message"] == "Name required"

    payload = _get_packet(received_whitespace, "error")
    assert payload is not None, f"Got: {received_whitespace}"
    assert payload["message"] == "Name required"

    # Assert: in-memory state not updated
    assert len(rooms.ROOMS) == 0


def test_create_multiple_rooms_success(make_sios):
    # Setup
    clients = make_sios(100)

    for i in range(100):
        # Act
        sio = clients[i]
        sio.emit("create_room", {"name": "Alice"})
        received = sio.get_received()

        # Assert: event output
        payload = _get_packet(received, "room_created")
        assert payload is not None, f"Got: {received}"
        assert payload["host_name"] == "Alice"
        assert payload["participants"] == ["Alice"]

    # Assert: in-memory state updated w/ 100 unique rooms
    assert len(rooms.ROOMS) == 100
    assert len(rooms.SID_TO_RID) == 100


# ------------ Join room tests ------------
def test_join_room_success(make_sios):
    # Setup
    sio_host, sio_participant = make_sios(2)

    sio_host.emit("create_room", {"name": "Alice"})
    received = sio_host.get_received()
    rid = _get_packet(received, "room_created")["room_id"]

    # Act
    sio_participant.emit("join_room", {"room_id": rid, "name": "Bob"})
    received = sio_participant.get_received()

    # Assert: event output
    payload = _get_packet(received, "joined")
    assert payload is not None, f"Got: {received}"
    assert payload["name"] == "Bob"

    payload = _get_packet(received, "room_update")
    assert payload is not None, f"Got: {received}"
    assert payload["room_id"] == rid
    assert payload["participants"] == ["Alice", "Bob"]
    assert payload["host_name"] == "Alice"

    # Assert: in-memory state updated
    room = rooms.ROOMS[payload["room_id"]]
    assert len(rooms.ROOMS) == 1
    assert room.host.name == payload["host_name"]
    assert [p.name for p in room.participants] == ["Alice", "Bob"]

    assert len(rooms.SID_TO_RID) == 2
    for sid in rooms.SID_TO_RID:
        assert rooms.SID_TO_RID[sid] == payload["room_id"]


def test_join_room_without_rid(sio):
    # Act
    sio.emit("join_room", {"name": "Bob"})
    received_no_rid = sio.get_received()
    sio.emit("join_room", {"room_id": "    \n \t ", "name": "Bob"})
    received_whitespace_rid = sio.get_received()

    # Assert: event output
    payload = _get_packet(received_no_rid, "error")
    assert payload is not None, f"Got: {received_no_rid}"
    assert payload["message"] == "Room ID required"

    payload = _get_packet(received_whitespace_rid, "error")
    assert payload is not None, f"Got: {received_whitespace_rid}"
    assert payload["message"] == "Room ID required"


def test_join_room_with_wrong_rid(sio):
    # Act
    sio.emit("join_room", {"room_id": "rgfjosrj", "name": "Bob"})
    received = sio.get_received()

    # Assert: event output
    payload = _get_packet(received, "error")
    assert payload is not None, f"Got: {received}"
    assert payload["message"] == "Room not found"


def test_join_room_without_name(make_sios):
    # Setup
    sio_host, sio_participant = make_sios(2)

    sio_host.emit("create_room", {"name": "Alice"})
    received = sio_host.get_received()
    rid = _get_packet(received, "room_created")["room_id"]

    # Act
    sio_participant.emit("join_room", {"room_id": rid})
    received_no_name = sio_participant.get_received()
    sio_participant.emit("join_room", {"room_id": rid, "name": "   \t \n    "})
    received_whitespace_name = sio_participant.get_received()

    # Assert: event output
    payload = _get_packet(received_no_name, "error")
    assert payload is not None, f"Got: {received_no_name}"
    assert payload["message"] == "Name required"

    payload = _get_packet(received_whitespace_name, "error")
    assert payload is not None, f"Got: {received_whitespace_name}"
    assert payload["message"] == "Name required"


def test_join_room_with_duplicate_name(make_sios):
    # Setup
    sio_host, sio_participant = make_sios(2)

    sio_host.emit("create_room", {"name": "Alice"})
    received = sio_host.get_received()
    rid = _get_packet(received, "room_created")["room_id"]

    # Act
    sio_participant.emit("join_room", {"room_id": rid, "name": "Alice"})
    received = sio_participant.get_received()

    # Assert: event output
    payload = _get_packet(received, "error")
    assert payload is not None, f"Got: {received}"
    assert payload["message"] == "Name already taken"


def test_multiple_join_room_success(make_sios):
    # Setup
    clients = make_sios(101)
    sio_host = clients[100]

    sio_host.emit("create_room", {"name": "Alice"})
    received = sio_host.get_received()
    rid = _get_packet(received, "room_created")["room_id"]

    for i in range(100):
        # Act
        sio_participant = clients[i]
        sio_participant.emit("join_room", {"room_id": rid, "name": str(i)})
        received = sio_participant.get_received()

        # Assert: event output
        payload = _get_packet(received, "joined")
        assert payload is not None, f"Got: {received}"
        assert payload["name"] == str(i)

        payload = _get_packet(received, "room_update")
        assert payload is not None, f"Got: {received}"
        assert payload["participants"] == ["Alice"] + [str(i) for i in range(i + 1)]
        assert payload["host_name"] == "Alice"

    # Assert: in-memory state updated w/ 101 unique participants
    assert len(rooms.ROOMS) == 1
    assert len(rooms.ROOMS[rid].participants) == 101
    assert len(rooms.SID_TO_RID) == 101


# ------------ Helpers ------------
def _get_packet(received, name: str):
    for pkt in received:
        if pkt.get("name") == name:
            # test_client packs event args in a list
            args = pkt.get("args") or []
            return args[0] if args else None
    return None
