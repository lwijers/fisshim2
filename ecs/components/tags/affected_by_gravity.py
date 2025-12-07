# ecs/components/affected_by_gravity.py
from dataclasses import dataclass

@dataclass
class AffectedByGravity:
    """Marks an entity that should fall vertically in logical space."""
    speed: float = 55.0  # logical px/sec (override per-entity as needed)
