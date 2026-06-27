import json
import os


class DialogueLoader:

    def __init__(self, json_path: str):

        base_dir = os.path.dirname(os.path.abspath(__file__))
        full_path = os.path.join(base_dir, "..", json_path)
        full_path = os.path.normpath(full_path)

        with open(full_path, "r", encoding="utf-8") as file:
            raw = json.load(file)

        if isinstance(raw, dict):
            self.dialogues = raw.get("dialogues", [])
        else:
            self.dialogues = raw

        self.dialogues = [
            d for d in self.dialogues
            if isinstance(d, dict)
        ]

    def get_dialogues(self):
        return self.dialogues