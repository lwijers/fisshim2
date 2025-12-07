# ecs/components/food_pellet_component.py

from dataclasses import dataclass

@dataclass
class FoodPellet:
    """
    Marks a falling food pellet and carries gameplay tuning attached to the pellet.
    - nutrition: fullness restored when eaten
    - radius_scale: multiplies the sprite's base radius for collision/vision
    - center_off_x/y: pixel offsets in *logical space* for visual/art centering
    """
    nutrition: float = 40.0
    radius_scale: float = 1.0
    center_off_x: float = 0.0
    center_off_y: float = 0.0
