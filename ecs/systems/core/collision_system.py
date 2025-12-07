# ecs/systems/collision_system.py
from ecs.components.core.position_component import Position
from ecs.components.core.velocity_component import Velocity
from ecs.components.core.sprite_component import Sprite
from ecs.components.core.tank_ref_component import TankRef
from ecs.components.tags.dead_component import DeadFlag

class CollisionSystem:
    """
    Enforces hard tank boundaries and applies bounce to velocity when colliding.
    MovementSystem no longer does any clamping/bounce; it only integrates.
    """
    def __init__(self, context):
        self.context = context
        self.wall_bounce = float((context.balancing or {}).get("wall_bounce", 0.35))

    def update(self, world, dt):
        lw = self.context.logical_tank_w
        lh = self.context.logical_tank_h
        swim_floor = float(getattr(self.context, "swim_bottom_margin", 64))
        alive_bottom_y = lh - swim_floor  # top of dark brown frame

        for e in world.entities_with(Position, Velocity, Sprite, TankRef):
            if world.get_component(e, DeadFlag):
                # dead: keep existing full-tank clamp (GravitySystem settles them on sand)
                pos = world.get_component(e, Position)
                spr = world.get_component(e, Sprite)
                if pos.x < 0: pos.x = 0
                if pos.x + spr.base_w > lw: pos.x = lw - spr.base_w
                if pos.y < 0: pos.y = 0
                if pos.y + spr.base_h > lh: pos.y = lh - spr.base_h
                continue

            pos = world.get_component(e, Position)
            vel = world.get_component(e, Velocity)
            spr = world.get_component(e, Sprite)

            # left/right/top (unchanged) ...
            if pos.x < 0.0:
                pos.x = 0.0
                if vel.dx < 0.0: vel.dx = -vel.dx * self.wall_bounce
            if pos.x + spr.base_w > lw:
                pos.x = lw - spr.base_w
                if vel.dx > 0.0: vel.dx = -vel.dx * self.wall_bounce
            if pos.y < 0.0:
                pos.y = 0.0
                if vel.dy < 0.0: vel.dy = -vel.dy * self.wall_bounce

            # bottom → clamp to the swim floor (not the tank bottom)
            bottom_limit = max(0.0, alive_bottom_y - spr.base_h)
            if pos.y > bottom_limit:
                pos.y = bottom_limit
                if vel.dy > 0.0:
                    vel.dy = -vel.dy * self.wall_bounce

