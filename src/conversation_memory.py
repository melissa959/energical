from typing import Optional


class ConversationMemory:

    def __init__(self):
        self.reset()

    def reset(self):
        self.category: Optional[str] = None
        self.sous_categorie: Optional[str] = None
        self.budget: Optional[int] = None
        self.capacity: Optional[int] = None
        # ── NEW: decision tree fields ─────────────────────
        self.surface_m2: Optional[int] = None
        self.region: Optional[str] = None
        self.energie: Optional[str] = None
        self.usage: Optional[str] = None
        self.condensation: Optional[str] = None
        # ─────────────────────────────────────────────────

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
            # ── NEW ──────────────────────────────────────
            "surface_m2":    self.surface_m2,
            "region":        self.region,
            "energie":       self.energie,
            "usage":         self.usage,
            "condensation":  self.condensation,
            # ─────────────────────────────────────────────
        }

    def to_prompt(self) -> str:
        filled = {k: v for k, v in self.to_dict().items() if v is not None}
        if not filled:
            return "No conversation memory yet."
        return "\n".join(f"{k}: {v}" for k, v in filled.items())