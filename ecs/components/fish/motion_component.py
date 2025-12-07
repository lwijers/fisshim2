from dataclasses import dataclass

@dataclass
class MotionParams:
    max_speed: float = 40.0
    acceleration: float = 30.0
    turn_speed: float = 3.0       # radians/sec or normalized
    dart_multiplier: float = 2.5  # for the Dart state
