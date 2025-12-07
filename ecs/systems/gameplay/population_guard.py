from ecs.components.fish.brain_component import Brain
from ecs.components.tags.dead_component import DeadFlag

class PopulationGuard:
    """
    Maintains ctx.population_ok by counting living (Brain & !DeadFlag).
    Why: gate breeding completion and eligibility.
    """
    def __init__(self, context):
        self.ctx = context

    def update(self, world, dt):
        living = 0
        for e in world.entities_with(Brain):
            if world.get_component(e, DeadFlag) is None:
                living += 1
        self.ctx.population_ok = (living < int(self.ctx.breeding["max_population"]))