from dataclasses import dataclass

@dataclass
class Hunger:
    hunger: float = 0.0
    hunger_rate: float = 0.02
    hunger_max: float = 100.0
