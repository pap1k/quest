from telebot.types import Message


class Confirmation:
    messages: list[Message] = 0
    from_id: int = 0

    def __init__(self, id) -> None:
        self.from_id = id
        self.messages = []
