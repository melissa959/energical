from typing import List, Dict


class ChatHistory:

    def __init__(self):
        self.messages: List[Dict[str, str]] = []

    def add_user(self, message: str):
        self.messages.append({"role": "user", "content": message})

    def add_assistant(self, message: str):
        self.messages.append({"role": "assistant", "content": message})

    def get_history(self) -> List[Dict[str, str]]:
        return self.messages

    def clear(self):
        self.messages.clear()