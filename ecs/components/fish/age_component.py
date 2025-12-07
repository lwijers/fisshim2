# [ecs/components/age_component.py] — lifespan starts at hatch; egg has its own timer
from dataclasses import dataclass

@dataclass
class Age:
    # Age that counts toward lifespan (starts at 0 once hatched)
    age: float = 0.0
    lifespan: float = 400.0

    # Life stage: "Egg" (pre-hatch, not aging), then "Juvenile"/"Adult"/"Senior"
    # Default to "Juvenile" so existing fish spawn hatched and moving.
    stage: str = "Juvenile"

    # Time spent as an egg (seconds). Does NOT count toward lifespan.
    pre_hatch: float = 0.0
