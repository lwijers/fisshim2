from dataclasses import dataclass
@dataclass
class SteeringIntent:
    dx: float = 0.0
    dy: float = 0.0  # reset every frame by MovementSystem