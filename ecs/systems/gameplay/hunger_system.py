# ecs/systems/hunger_system.py

from ecs.components.fish.hunger_component import Hunger
from ecs.components.fish.health_component import Health
from ecs.components.tags.dead_component import DeadFlag

class HungerSystem:
    """
    Per-fish hunger decay.

    Each fish has:
        hunger.hunger       (0 .. hunger_max)
        hunger.hunger_rate  (per second)
        hunger.hunger_max   (species or default)

    When hunger hits 0 → health drains in HealthSystem, not here.
    """

    def update(self, world, dt):
        for e in world.entities_with(Hunger, Health):
            if world.get_component(e, DeadFlag):
                continue
            hunger = world.get_component(e, Hunger)

            # Reduce hunger
            hunger.hunger -= hunger.hunger_rate * dt

            # Clamp
            if hunger.hunger < 0:
                hunger.hunger = 0
            if hunger.hunger > hunger.hunger_max:
                hunger.hunger = hunger.hunger_max
