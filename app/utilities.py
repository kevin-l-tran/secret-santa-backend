import secrets
import string

from typing import TypedDict


# ------------ Room & participant classes ------------
class Participant(TypedDict):
    sid: str
    name: str


class Room:
    def __init__(self, id: str, host: Participant):
        self.id = id
        self.host = host
        self.participants = [host]

    def __eq__(self, other: any) -> bool:
        if not isinstance(other, Room):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)

    def add_member(self, participant: Participant) -> bool:
        if participant.name not in [p.name for p in self.participants]:
            self.participants.append(participant)
            return True
        else:
            return False


# ------------ Helpers ------------
def new_code(n):
    alphabet = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(n))


def knuth_shuffle(list: list[any]):
    length = len(list)
    for i in range(0, length - 1):
        j = secrets.choice(range(i, length))
        list[i], list[j] = list[j], list[i]
    return list
