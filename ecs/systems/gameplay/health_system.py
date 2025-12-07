# ecs/systems/health_system.py

from ecs.components.fish.health_component import Health
from ecs.components.fish.hunger_component import Hunger
from ecs.components.fish.behavior_tuning import BehaviorTuning
from ecs.components.tags.dead_component import DeadFlag
from ecs.components.fish.age_component import Age
class HealthSystem:
    """
    Handles health regeneration and starvation.
    Does NOT change AI state directly — sets DeadFlag instead.
    """

    def update(self, world, dt):
        for e in world.entities_with(Health, Hunger, BehaviorTuning):
            if world.get_component(e, DeadFlag):
                continue
            health = world.get_component(e, Health)
            hunger = world.get_component(e, Hunger)
            tuning = world.get_component(e, BehaviorTuning)

            regen_factor = tuning.get("health_regen_factor", 0.0)
            starve_factor = tuning.get("health_starve_factor", 0.0)
            regen_threshold = tuning.get("health_regen_threshold", 0.5)

            hunger_ratio = hunger.hunger / hunger.hunger_max

            # Regeneration
            if hunger_ratio > regen_threshold:
                health.value = min(
                    health.max_value,
                    health.value + health.max_value * regen_factor * dt
                )

            # Starvation damage
            if hunger.hunger <= 0:
                health.value -= health.max_value * starve_factor * dt

            # Mark death (but do not change AI state!)
            if health.value <= 0:
                if not world.get_component(e, DeadFlag):
                    world.add_component(e, DeadFlag())
                # NEW: reflect death in the life-stage component
                age = world.get_component(e, Age)
                if age is not None:
                    age.stage = "Dead"