class BaseState:
    NAME = "Base"
    def enter(self, fish, context): pass
    def exit(self, fish, context): pass
    def update(self, fish, speed_intent, context, dt, world):
        raise NotImplementedError
    def set_target(self, fish, tx, ty):
        fish.brain.tx = tx; fish.brain.ty = ty
        fish.target.tx = tx; fish.target.ty = ty