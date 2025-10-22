import app.rooms as rooms


# ------------ Create room tests ------------
def test_create_room_success(sio):
    # Act
    sio.emit("create_room", {"name": "Alice"})
    received = sio.get_received()

    # Assert: event output
    payload = _get_packet(received, "room_created")
    assert payload is not None and f"Got: {received}"
    assert payload["host_name"] == "Alice"
    assert payload["participants"] == ["Alice"]

    # Assert: in-memory state updated
    room = rooms.ROOMS[payload["room_id"]]
    assert len(rooms.ROOMS) == 1
    assert room.id == payload["room_id"]
    assert [p.name for p in room.participants] == ["Alice"]


def test_create_room_without_name(sio):
    # Act
    sio.emit("create_room", {})
    received_no_name = sio.get_received()
    sio.emit("create_room", {"name": "    "})
    received_whitespace = sio.get_received()

    # Assert: event output
    payload = _get_packet(received_no_name, "error")
    assert payload is not None and f"Got: {received_no_name}"
    assert payload["message"] == "Name required"

    payload = _get_packet(received_whitespace, "error")
    assert payload is not None and f"Got: {received_whitespace}"
    assert payload["message"] == "Name required"

    # Assert: in-memory state not updated
    assert len(rooms.ROOMS) == 0


def test_create_multiple_rooms_success(sio):
    # Act
    for i in range(1000):
        sio.emit("create_room", {"name": "Alice"})
        received = sio.get_received()

        # Assert: event output
        payload = _get_packet(received, "room_created")
        assert payload is not None, f"Got: {received}"
        assert payload["host_name"] == "Alice"
        assert payload["participants"] == ["Alice"]
    
    # Assert: in-memory state updated w/ 1000 unique rooms
    assert len(rooms.ROOMS) == 1000


# ------------ Helpers ------------
def _get_packet(received, name: str):
    for pkt in received:
        if pkt.get("name") == name:
            # test_client packs event args in a list
            args = pkt.get("args") or []
            return args[0] if args else None
    return None