from dataclasses import dataclass, field


@dataclass
class Dialog:
    role: str
    prompt: str
    answer: str


@dataclass
class Chat:
    ticket_nr: int
    dialogs: list[Dialog] = field(default_factory=list)

    def add_dialog(
        self,
        role: str,
        prompt: str,
        answer: str
    ) -> Dialog:
        dialog = Dialog(
            role=role,
            prompt=prompt,
            answer=answer
        )

        self.dialogs.append(dialog)

        return dialog


@dataclass
class Conversation:
    chats: list[Chat] = field(default_factory=list)

    def create_chat(self, ticket_nr: int) -> Chat:
        chat = Chat(ticket_nr=ticket_nr)

        self.chats.append(chat)

        return chat