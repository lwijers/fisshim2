from dataclasses import dataclass

@dataclass
class TankStats:
    temperature: float = 22.0
    cleanliness: float = 1.0
    capacity: int = 50