# ecs/systems/gravity_system.py
from ecs.components.tags.affected_by_gravity import AffectedByGravity
from ecs.components.core.position_component import Position
from ecs.components.core.sprite_component import Sprite
from ecs.components.core.tank_ref_component import TankRef

class GravitySystem:
    """
    Single, generic falling system for pellets, eggs, dead fish, etc.
    Applies +Y based on AffectedByGravity.speed until resting on the sand.
    """
    def __init__(self, context):
        self.context = context

    def _floor_logical_y(self) -> float:
        """Top of sand in logical coords."""
        logical_h = self.context.logical_tank_h
        px = getattr(self.context, "sand_top_px", -1)
        if px is not None and px >= 0:
            return min(logical_h, float(px))
        r = float(getattr(self.context, "sand_top_ratio", 1.0))
        return logical_h * max(0.0, min(1.0, r))

    def update(self, world, dt: float) -> None:
        if dt <= 0.0:
            return
        floor_y = self._floor_logical_y()
        for e in world.entities_with(AffectedByGravity, Position, Sprite, TankRef):
            grav = world.get_component(e, AffectedByGravity)
            pos = world.get_component(e, Position)
            spr = world.get_component(e, Sprite)

            pos.y += float(grav.speed) * dt
            rest_y = floor_y - spr.base_h
            if pos.y > rest_y:
                pos.y = rest_y
