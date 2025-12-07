# ecs/components/tank_component.py

from dataclasses import dataclass


@dataclass
class Tank:
    """Marker component to tag an entity as a tank."""
    pass
