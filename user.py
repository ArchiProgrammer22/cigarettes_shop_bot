from dataclasses import dataclass


@dataclass
class User:
    room: int
    product: str = ''
    phone: str = ''
    call_or_message: str = ''
