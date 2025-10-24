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


def test_create_emit_does_not_leak(make_sios):
    # Setup
    host1, host2 = make_sios(2)
    host1.emit("create_room", {"name": "Alice"})
    host1.get_received()  # clear host1 queue

    # Act
    host2.emit("create_room", {"name": "Carol"})

    # Assert: host1 gets nothing
    a_batch = host1.get_received()
    assert _get_packet(a_batch, "room_created") is None

    # Assert: host2 gets events
    b_batch = host2.get_received()
    assert _get_packet(b_batch, "room_created") is not None


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


def test_join_emit_does_not_leak(make_sios):
    # Setup
    host1, participant, host2 = make_sios(3)
    host1.emit("create_room", {"name": "Alice"})

    # Act
    host2.emit("create_room", {"name": "Carol"})
    received = host2.get_received()
    rid = _get_packet(received, "room_created")["room_id"]
    participant.emit("join_room", {"room_id": rid, "name": "Bob"})

    # Assert: host1 gets nothing
    a_batch = host1.get_received()
    assert _get_packet(a_batch, "joined") is None

    # Assert: host2 gets events
    b_batch = host2.get_received()
    assert _get_packet(b_batch, "joined") is not None


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


# ------------ Leave room tests ------------
def test_disconnect_without_a_room(sio):
    # Act
    sio.disconnect()

    # Assert: in-memory state unchanged
    assert len(rooms.ROOMS) == 0
    assert len(rooms.SID_TO_RID) == 0


def test_leave_room_with_single_participant(sio):
    # Setup
    sio.emit("create_room", {"name": "Alice"})

    # Act
    sio.disconnect()

    # Assert: in-memory state unchanged
    assert len(rooms.ROOMS) == 0
    assert len(rooms.SID_TO_RID) == 0


def test_participant_leaves_room(make_sios):
    # Setup
    sio_host, sio_participant = make_sios(2)

    sio_host.emit("create_room", {"name": "Alice"})
    received = sio_host.get_received()
    payload = _get_packet(received, "room_created")
    rid = payload["room_id"]

    sio_participant.emit("join_room", {"room_id": rid, "name": "Bob"})

    # Drain host queue so we ignore the "Alice+Bob" room_update from join
    sio_host.get_received()

    # Act
    sio_participant.disconnect()

    # Assert: event output
    received = sio_host.get_received()

    payload = _get_packet(received, "disconnected")
    assert payload is not None, f"Got: {received}"
    assert payload["name"] == "Bob"

    payload = _get_packet(received, "room_update")
    assert payload is not None, f"Got: {received}"
    assert payload["room_id"] == rid
    assert payload["participants"] == ["Alice"]
    assert payload["host_name"] == "Alice"

    # Assert: in-memory state updated
    room = rooms.ROOMS[payload["room_id"]]
    assert len(rooms.ROOMS) == 1
    assert len(rooms.ROOMS[rid].participants) == 1
    assert len(rooms.SID_TO_RID) == 1
    assert room.host.name == payload["host_name"]
    assert [p.name for p in room.participants] == ["Alice"]


def test_host_leaves_room(make_sios):
    # Setup
    sio_host, sio_participant = make_sios(2)

    sio_host.emit("create_room", {"name": "Alice"})
    received = sio_host.get_received()
    payload = _get_packet(received, "room_created")
    rid = payload["room_id"]

    sio_participant.emit("join_room", {"room_id": rid, "name": "Bob"})

    sio_participant.get_received()  # clear participant queue

    # Act
    sio_host.disconnect()

    # Assert: event output
    received = sio_participant.get_received()

    payload = _get_packet(received, "host_changed")
    assert payload is not None, f"Got: {received}"
    assert payload["host_name"] == "Bob"

    payload = _get_packet(received, "disconnected")
    assert payload is not None, f"Got: {received}"
    assert payload["name"] == "Alice"

    payload = _get_packet(received, "room_update")
    assert payload is not None, f"Got: {received}"
    assert payload["room_id"] == rid
    assert payload["participants"] == ["Bob"]
    assert payload["host_name"] == "Bob"

    # Assert: in-memory state updated
    room = rooms.ROOMS[payload["room_id"]]
    assert len(rooms.ROOMS) == 1
    assert len(rooms.ROOMS[rid].participants) == 1
    assert len(rooms.SID_TO_RID) == 1
    assert room.host.name == payload["host_name"]
    assert [p.name for p in room.participants] == ["Bob"]


def test_disconnect_emit_does_not_leak(make_sios):
    # Setup
    host1, guest, host2 = make_sios(3)

    host1.emit("create_room", {"name": "Alice"})
    rid_a = _get_packet(host1.get_received(), "room_created")["room_id"]

    guest.emit("join_room", {"room_id": rid_a, "name": "Bob"})
    host1.get_received()  # clear host1 queue

    host2.emit("create_room", {"name": "Carol"})

    # Act
    guest.disconnect()

    # Assert: host1 gets events
    a_batch = host1.get_received()
    assert _get_packet(a_batch, "disconnected")["name"] == "Bob"
    assert _get_packet(a_batch, "room_update") is not None

    # Assert: host2 gets nothing
    b_batch = host2.get_received()
    assert _get_packet(b_batch, "disconnected") is None
    assert _get_packet(b_batch, "room_update") is None


def test_multiple_disconnects_success(make_sios):
    # Setup
    hosts = make_sios(10)
    participants = make_sios(100)

    for i, host in enumerate(hosts):
        host.emit("create_room", {"name": "Alice"})
        rid = _get_packet(host.get_received(), "room_created")["room_id"]

        group = participants[i * 10 : (i + 1) * 10]
        for p in group:
            p.emit("join_room", {"room_id": rid, "name": "Bob"})

    # Act
    for host in hosts:
        host.disconnect()
    for participant in participants:
        participant.disconnect()

    # Assert: in-memory state unchanged
    assert len(rooms.ROOMS) == 0
    assert len(rooms.SID_TO_RID) == 0


# ------------ Helpers ------------
def _get_packet(received, name: str):
    for pkt in received:
        if pkt.get("name") == name:
            # test_client packs event args in a list
            args = pkt.get("args") or []
            return args[0] if args else None
    return None
