# ecs/fsm/egg_state.py
from ecs.fsm.base_state import BaseState

class EggState(BaseState):
    NAME = "Egg"

    def enter(self, fish, context):
        b = fish.brain
        b.current_desired_speed = 0.0
        # Sit still: keep target at current logical position
        self.set_target(fish, fish.pos.x, fish.pos.y)

    def update(self, fish, speed_intent, context, dt, world):
        # Eggs do not move/swim; GravitySystem handles falling.
        speed_intent.desired_speed = 0.0
        # Maintain target at current spot so steering stays neutral.
        self.set_target(fish, fish.pos.x, fish.pos.y)
        # No transition decision here — StateOverrideSystem handles leaving Egg
        # when Age.stage != "Egg".
        return None
