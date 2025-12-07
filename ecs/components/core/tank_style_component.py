# ecs/components/tank_style_component.py

from dataclasses import dataclass


@dataclass
class TankStyle:
    border_color: tuple = (20, 40, 80)
    thickness: int = 6
    padding: int = 0  # if you want tank slightly inset from screen edges later
