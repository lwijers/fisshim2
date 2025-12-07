import random, math
from ecs.fsm.base_state import BaseState
class IdleState(BaseState):
    NAME = "Idle"
    def enter(self, fish, context):
        b = fish.brain; t = fish.tuning
        b.state_timer = 0.0
        b._min = t.get("idle_min_time"); b._max = t.get("idle_max_time")
        b._speed_factor = t.get("idle_speed_factor")
        b._amp = t.get("idle_bob_amplitude"); b._freq = t.get("idle_bob_frequency")
        b.idle_origin_x = fish.pos.x; b.idle_origin_y = fish.pos.y
        self._pick_new_idle_target(fish, context)
        b.next_state_time = b._min + random.uniform(0.0, 3.0)
    def _pick_new_idle_target(self, fish, context):
        b = fish.brain; amp = b._amp
        tx = max(0, min(context.logical_tank_w, b.idle_origin_x + random.uniform(-amp, amp)))
        ty = max(0, min(context.logical_tank_h, b.idle_origin_y + random.uniform(-amp, amp)))
        self.set_target(fish, tx, ty)
    def update(self, fish, speed_intent, context, dt, world):
        b = fish.brain; pos = fish.pos
        b.state_timer += dt
        amp, freq = b._amp, b._freq
        fx = float(context.balancing.get("idle_bob_x_factor", 1.0))
        fy = float(context.balancing.get("idle_bob_y_factor", 0.8))
        sx = math.sin(b.state_timer * freq) * (amp * 0.25) * fx
        sy = math.cos(b.state_timer * freq * 0.8) * (amp * 0.25) * fy
        self.set_target(fish, b.tx + sx, b.ty + sy)
        smooth = float(context.balancing.get("state_speed_smoothing", 0.10))
        target_speed = fish.motion.max_speed * b._speed_factor
        b.current_desired_speed += (target_speed - b.current_desired_speed) * smooth
        speed_intent.desired_speed = b.current_desired_speed
        if b.state_timer > b._max: return "Cruise"
        if b.state_timer > b.next_state_time:
            import random as _r
            if _r.random() < fish.tuning.get("transition_to_cruise_chance") * _r.uniform(0.7, 1.3):
                return "Cruise"
        return None