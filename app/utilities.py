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

    def add_member(self, participant: Participant) -> bool:
        if participant.name not in [p.name for p in self.participants]:
            self.participants.append(participant)
            return True
        else:
            return False
