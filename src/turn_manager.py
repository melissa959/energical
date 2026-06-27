class TurnManager:

    def __init__(self):
        self.turn_count = 0

    def increment(self):
        self.turn_count += 1

    def reset(self):
        self.turn_count = 0

    def get_turn_count(self) -> int:
        return self.turn_count