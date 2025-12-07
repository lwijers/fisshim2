# ecs/systems/renderers/__init__.py
"""
Convenience re-exports for renderer helpers and caches.
"""

from .cache import LabelCache, SpriteCache
from .geometry import (
    center_logical,
    pellet_center_radius,
    mouth_logical,
    mouth_radius_from_tuning,
    vision_radius_from_tuning,
)
from .draw_sprite import choose_facing, draw_sprite
from .overlay_labels import draw_state_and_bars
from .overlay_food import draw_food_debug, draw_target_line_from_mouth
from .overlay_motion import draw_velocity_arrow, draw_avoidance_arrow

__all__ = [
    "LabelCache",
    "SpriteCache",
    "center_logical",
    "pellet_center_radius",
    "mouth_logical",
    "mouth_radius_from_tuning",
    "vision_radius_from_tuning",
    "choose_facing",
    "draw_sprite",
    "draw_state_and_bars",
    "draw_food_debug",
    "draw_target_line_from_mouth",
    "draw_velocity_arrow",
    "draw_avoidance_arrow",
]
