import secrets
import string

from dataclasses import dataclass


# ------------ Room & participant classes ------------
@dataclass
class Participant:
    sid: str
    name: str


class Room:
    def __init__(self, id: str, host: Participant):
        self.id = id
        self.host = host
        self.participants = [host]

    def add_member(self, participant: Participant) -> bool:
        if participant.name not in [p.name for p in self.participants]:
            self.participants.append(participant)
            return True
        else:
            return False


# ------------ Helpers ------------
def new_code(n):
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(n))


def knuth_shuffle(list: list[any]):
    length = len(list)
    for i in range(0, length - 1):
        j = secrets.choice(range(i, length))
        list[i], list[j] = list[j], list[i]
    return list
