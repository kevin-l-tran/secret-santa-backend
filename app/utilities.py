import secrets
import string

from dataclasses import dataclass


# ------------ Room & participant classes ------------
@dataclass
class Participant:
    sid: str
    name: str


class Room:
    def __init__(self, host: Participant) -> None:
        self.host = host
        self.participants = [host]

    def add_member(self, participant: Participant) -> bool:
        if participant.name not in [p.name for p in self.participants]:
            self.participants.append(participant)
            return True
        else:
            return False


# ------------ Helpers ------------
def new_code(n) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(n))


def knuth_shuffle[T](ls: list[T]) -> list[T]:
    length = len(ls)
    for i in range(0, length - 1):
        j = secrets.choice(range(i+1, length))
        ls[i], ls[j] = ls[j], ls[i]
    return ls
