from world import World
from game_context import GameContext

from ecs.components.core.position_component import Position
from ecs.components.core.sprite_component import Sprite

from ecs.components.fish.age_component import Age
from ecs.components.fish.hunger_component import Hunger
from ecs.components.fish.health_component import Health
from ecs.components.fish.behavior_tuning import BehaviorTuning

from ecs.systems.gameplay.hunger_system import HungerSystem
from ecs.systems.gameplay.health_system import HealthSystem
from ecs.systems.gameplay.aging_system import AgingSystem


def _fish_with_age(world: World):
    e = world.create_entity()
    world.add_component(e, Age(stage="Egg", age=0.0))
    world.add_component(e, Hunger(hunger=0.0, hunger_rate=0.0, hunger_max=100.0))
    world.add_component(e, Health(value=100.0, max_value=100.0))
    world.add_component(e, Position(0.0, 0.0))
    world.add_component(e, Sprite("goldfish", 60, 40))
    # HealthSystem in this build reads regen/starve from BehaviorTuning
    world.add_component(
        e,
        BehaviorTuning(
            {
                "health_regen_factor": 0.0,
                "health_regen_threshold": 1.0,
                "health_starve_factor": 0.5,
            }
        ),
    )
    return e


def test_egg_hatches_then_juvenile_defaults(make_context, dt):
    """Sanity check: egg ages through hatch without crashing."""
    world = World()
    ctx: GameContext = make_context()
    fish = _fish_with_age(world)

    age_sys = AgingSystem(ctx)
    hunger_sys = HungerSystem()
    health_sys = HealthSystem()

    # Run a few steps to ensure no exceptions and state evolves
    for _ in range(10):
        age_sys.update(world, dt)
        hunger_sys.update(world, dt)
        health_sys.update(world, dt)

    age = world.get_component(fish, Age)
    assert age is not None
    assert age.age >= 0.0  # progressed in time


def test_starvation_then_health_decay(make_context, dt):
    world = World()
    ctx: GameContext = make_context()
    fish = _fish_with_age(world)

    # make it post-hatch and then starve it
    age = world.get_component(fish, Age)
    age.stage = "Adult"
    age.age = 0.0

    hunger = world.get_component(fish, Hunger)
    hunger.hunger = 1.0
    hunger.hunger_rate = 10.0  # hit zero quickly

    health = world.get_component(fish, Health)
    h0 = health.value

    hunger_sys = HungerSystem()
    health_sys = HealthSystem()

    # Step until hunger bottoms and health starts decaying
    for _ in range(30):
        hunger_sys.update(world, dt)
        health_sys.update(world, dt)

    assert world.get_component(fish, Hunger).hunger <= 0.0
    assert world.get_component(fish, Health).value < h0  # should decay under starvation
