from typing import Optional


class ConversationMemory:

    def __init__(self):
        self.reset()

    def reset(self):
        self.category: Optional[str] = None
        self.sous_categorie: Optional[str] = None
        self.budget: Optional[int] = None
        self.capacity: Optional[int] = None

    def update(self, **kwargs):
        for key, value in kwargs.items():
            if value is not None and hasattr(self, key):
                setattr(self, key, value)

    def to_dict(self) -> dict:
        return {
            "category":      self.category,
            "sous_categorie": self.sous_categorie,
            "budget":        self.budget,
            "capacity":      self.capacity,
        }

    def to_prompt(self) -> str:
        filled = {k: v for k, v in self.to_dict().items() if v is not None}
        if not filled:
            return "No conversation memory yet."
        return "\n".join(f"{k}: {v}" for k, v in filled.items())