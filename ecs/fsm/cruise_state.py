import random
from math import hypot
from ecs.fsm.base_state import BaseState
class CruiseState(BaseState):
    NAME = "Cruise"

    def enter(self, fish, context):
        brain = fish.brain
        t = fish.tuning

        # Pull defaults from context.fish_defaults with safe fallbacks
        fd = getattr(context, "fish_defaults", {}) or {}
        cruise_min = t.get("cruise_min_time", fd.get("cruise_min_time", 6.0))
        cruise_max = t.get("cruise_max_time", fd.get("cruise_max_time", 16.0))
        arrival = t.get("cruise_arrival_radius", fd.get("cruise_arrival_radius", 40.0))
        speed_fac = t.get("cruise_speed_factor", fd.get("cruise_speed_factor", 0.6))
        leave_ch = t.get("transition_to_idle_chance", fd.get("transition_to_idle_chance", 0.01))

        brain.state_timer = 0.0
        brain._cruise_min = float(cruise_min)
        brain._cruise_max = float(cruise_max)
        brain._arrival = float(arrival)
        brain._speed_factor = float(speed_fac)
        brain._leave_chance = float(leave_ch)

        from random import uniform
        self.set_target(fish,
                        uniform(0, context.logical_tank_w),
                        uniform(0, context.logical_tank_h)
                        )
        brain.next_state_time = brain._cruise_min + uniform(0.0, 2.0)

    def update(self, fish, speed_intent, context, dt, world):
        b = fish.brain; pos = fish.pos
        if hypot(b.tx - pos.x, b.ty - pos.y) < b._arrival:
            self.set_target(fish,
                random.uniform(0, context.logical_tank_w),
                random.uniform(0, context.logical_tank_h)
            )
        smooth = float(context.balancing.get("state_speed_smoothing", 0.10))
        target_speed = fish.motion.max_speed * b._speed_factor
        b.current_desired_speed += (target_speed - b.current_desired_speed) * smooth
        speed_intent.desired_speed = b.current_desired_speed
        b.state_timer += dt
        if b.state_timer > b._cruise_max: return "Idle"
        if b.state_timer > b.next_state_time:
            import random as _r
            if _r.random() < b._leave_chance * _r.uniform(0.7, 1.3):
                return "Idle"
        return None
