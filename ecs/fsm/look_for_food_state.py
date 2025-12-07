import random
from math import hypot
from ecs.fsm.base_state import BaseState
from ecs.components.tags.food_pellet_component import FoodPellet
from ecs.components.core.position_component import Position
from ecs.components.core.sprite_component import Sprite
from ecs.components.core.tank_ref_component import TankRef
class LookForFoodState(BaseState):
    NAME = "LookForFood"
    def enter(self, fish, context):
        b = fish.brain; t = fish.tuning
        b.state_timer = 0.0
        b._speed_factor = float(t.get("look_for_food_speed_factor", 0.9))
        b._retarget_interval = 0.8; b._retarget_timer = 0.0
        b._target_pellet = None
        self.set_target(fish,
            random.uniform(0, context.logical_tank_w),
            random.uniform(0, context.logical_tank_h)
        )
    def _nearest_visible_pellet(self, world, fish_pos, fish_spr, radius):
        fx = fish_pos.x + fish_spr.base_w * 0.5; fy = fish_pos.y + fish_spr.base_h * 0.5
        nearest, best_d, best_cx, best_cy = None, float("inf"), None, None
        for e in world.entities_with(FoodPellet, Position, Sprite, TankRef):
            p = world.get_component(e, Position); s = world.get_component(e, Sprite)
            cx = p.x + s.base_w * 0.5; cy = p.y + s.base_h * 0.5
            pr = max(s.base_w, s.base_h) * 0.5
            d = hypot(cx - fx, cy - fy)
            if d <= radius + pr and d < best_d:
                nearest, best_d, best_cx, best_cy = e, d, cx, cy
        return nearest, best_cx, best_cy
    def update(self, fish, speed_intent, context, dt, world):
        b, pos, spr, t = fish.brain, fish.pos, fish.sprite, fish.tuning
        vision = float(t.get("food_detect_radius", 200.0))
        target_id, cx, cy = self._nearest_visible_pellet(world, pos, spr, vision)
        if target_id is not None:
            b._target_pellet = target_id
            b._target_pellet_cx = cx; b._target_pellet_cy = cy
            return "ChaseFood"
        b._retarget_timer += dt
        if b._retarget_timer >= b._retarget_interval:
            b._retarget_timer = 0.0
            self.set_target(fish,
                random.uniform(0, context.logical_tank_w),
                random.uniform(0, context.logical_tank_h)
            )
        smooth = float(context.balancing.get("state_speed_smoothing", 0.10))
        target_speed = fish.motion.max_speed * b._speed_factor
        b.current_desired_speed += (target_speed - b.current_desired_speed) * smooth
        speed_intent.desired_speed = b.current_desired_speed
        return None
