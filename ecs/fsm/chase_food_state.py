from ecs.fsm.base_state import BaseState
from ecs.components.tags.food_pellet_component import FoodPellet
from ecs.components.core.position_component import Position
from ecs.components.core.sprite_component import Sprite
from ecs.components.core.tank_ref_component import TankRef
from utils.geometry import get_mouth_logical
class ChaseFoodState(BaseState):
    NAME = "ChaseFood"
    @staticmethod
    def _pellet_center_and_radius(world, pellet_id):
        comps = getattr(world, "_components", {})
        if pellet_id not in comps: return None, None, None
        pos = world.get_component(pellet_id, Position)
        spr = world.get_component(pellet_id, Sprite)
        pellet = world.get_component(pellet_id, FoodPellet)
        if not pos or not spr or not pellet: return None, None, None
        cx = pos.x + spr.base_w * 0.5; cy = pos.y + spr.base_h * 0.5
        base_r = max(spr.base_w, spr.base_h) * 0.5
        pr = base_r * float(getattr(pellet, "radius_scale", 1.0))
        return cx, cy, pr

    @staticmethod
    def _mouth_radius(fish):
        factor = float(fish.tuning.get("mouth_radius_factor", 0.35))
        size = min(fish.sprite.base_w, fish.sprite.base_h)
        return max(4.0, size * factor * 0.5)
    @staticmethod
    def _nearest_pellet(world, from_x, from_y):
        nearest, best_d2 = None, None
        for pe in world.entities_with(FoodPellet, Position, Sprite, TankRef):
            ppos = world.get_component(pe, Position); pspr = world.get_component(pe, Sprite)
            cx = ppos.x + pspr.base_w * 0.5; cy = ppos.y + pspr.base_h * 0.5
            dx, dy = cx - from_x, cy - from_y
            d2 = dx*dx + dy*dy
            if best_d2 is None or d2 < best_d2: best_d2, nearest = d2, pe
        return nearest

    def enter(self, fish, context):
        b = fish.brain; t = fish.tuning
        b._speed_factor = float(t.get("chase_food_speed_factor", 1.0))
        b._target_pellet = None

    def update(self, fish, speed_intent, context, dt, world):
        b, t = fish.brain, fish.tuning
        fx = fish.pos.x + fish.sprite.base_w * 0.5
        fy = fish.pos.y + fish.sprite.base_h * 0.5
        target_pellet = self._nearest_pellet(world, fx, fy)
        if target_pellet is None:
            threshold = float(t.get("food_seek_threshold", 0.5))
            hungry = (fish.hunger.hunger / max(1e-6, fish.hunger.hunger_max)) < threshold
            return "LookForFood" if hungry else "Cruise"
        b._target_pellet = target_pellet
        pcx, pcy, pr = self._pellet_center_and_radius(world, target_pellet)
        if pcx is None:
            b._target_pellet = None; return None
        mx, my = get_mouth_logical(fish.pos, fish.sprite, target_x=pcx)
        mouth_r = self._mouth_radius(fish)
        eat_margin = float(t.get("eat_extra_margin", 6.0))
        self.set_target(fish, pcx, pcy)
        smooth = float(context.balancing.get("state_speed_smoothing", 0.10))
        target_speed = fish.motion.max_speed * b._speed_factor
        b.current_desired_speed += (target_speed - b.current_desired_speed) * smooth
        speed_intent.desired_speed = b.current_desired_speed
        dx, dy = pcx - mx, pcy - my
        dist = (dx*dx + dy*dy) ** 0.5
        if dist <= (pr + mouth_r + eat_margin):
            pellet = world.get_component(target_pellet, FoodPellet)
            nutrition = float(getattr(pellet, "nutrition", 40.0))
            audio = getattr(context, "audio", None)
            if audio:
                audio.play("bite")
            fish.hunger.hunger = min(fish.hunger.hunger_max, fish.hunger.hunger + nutrition)
            world.destroy_entity(target_pellet)
            b._target_pellet = None
            threshold = float(t.get("food_seek_threshold", 0.5))
            hungry = (fish.hunger.hunger / max(1e-6, fish.hunger.hunger_max)) < threshold
            return "LookForFood" if hungry else "Cruise"
        return None