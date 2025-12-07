# ecs/components/tank_label_component.py
from dataclasses import dataclass

@dataclass
class TankLabel:
    text: str = ""
    # Fallbacks; overridable from ui_config.json
    color: tuple = (255, 255, 255)
    size: int = 28
