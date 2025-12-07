# ecs/systems/renderers/geometry.py
from typing import Optional, Tuple
from ecs.components.core.position_component import Position
from ecs.components.core.sprite_component import Sprite
from ecs.components.tags.food_pellet_component import FoodPellet
from ecs.components.fish.behavior_tuning import BehaviorTuning
from utils.geometry import get_mouth_logical as _core_mouth_logical
def entity_exists(world, eid: int) -> bool:
    comps = getattr(world, "_components", None)
    return isinstance(comps, dict) and (eid in comps)

def center_logical(pos: Position, spr: Sprite) -> Tuple[float, float]:
    return pos.x + spr.base_w * 0.5, pos.y + spr.base_h * 0.5

def pellet_center_radius(world, pellet_id: int):
    if not entity_exists(world, pellet_id):
        return None, None, None
    pos = world.get_component(pellet_id, Position)
    spr = world.get_component(pellet_id, Sprite)
    pellet = world.get_component(pellet_id, FoodPellet)
    if not pos or not spr:
        return None, None, None
    cx = pos.x + spr.base_w * 0.5
    cy = pos.y + spr.base_h * 0.5
    base_r = max(spr.base_w, spr.base_h) * 0.5
    scale = float(getattr(pellet, "radius_scale", 1.0)) if pellet else 1.0
    pr = base_r * scale
    return cx, cy, pr

def mouth_logical(pos: Position, spr: Sprite, face_right: bool):
    # Backwards compat wrapper for existing renderer code
    return _core_mouth_logical(pos, spr, face_right=face_right)


def mouth_radius_from_tuning(spr: Sprite, tuning: Optional[BehaviorTuning]):
    factor = 0.35
    if tuning is not None:
        try:
            factor = float(tuning.get("mouth_radius_factor", factor))
        except Exception:
            pass
    size = min(spr.base_w, spr.base_h)
    return max(4.0, size * factor * 0.5)

def vision_radius_from_tuning(tuning: Optional[BehaviorTuning], default: float = 200.0) -> float:
    if tuning is None:
        return float(default)
    try:
        return float(tuning.get("food_detect_radius", default))
    except Exception:
        return float(default)
