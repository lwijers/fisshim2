from world import World
from game_context import GameContext

from ecs.components.core.position_component import Position
from ecs.components.core.velocity_component import Velocity
from ecs.components.core.sprite_component import Sprite
from ecs.components.core.tank_component import Tank
from ecs.components.core.tank_ref_component import TankRef

from ecs.components.fish.brain_component import Brain
from ecs.components.fish.motion_component import MotionParams
from ecs.components.fish.hunger_component import Hunger
from ecs.components.fish.behavior_tuning import BehaviorTuning
from ecs.components.fish.target_intent_component import TargetIntent
from ecs.components.fish.steering_intent_component import SteeringIntent
from ecs.components.fish.speed_intent_component import SpeedIntent

from ecs.components.tags.food_pellet_component import FoodPellet

from ecs.systems.ai.behavior_system import BehaviorSystem
from ecs.systems.ai.state_override_system import StateOverrideSystem
from ecs.systems.ai.state_transition_system import StateTransitionSystem
from ecs.systems.gameplay.hunger_system import HungerSystem
# We don't need MovementSystem for this test because we spawn the pellet
# inside the immediate eat radius.


def _tank(world: World):
    t = world.create_entity()
    world.add_component(t, Tank())
    world.add_component(t, Position(0.0, 0.0))
    return t


def _pellet_at(world: World, x: float, y: float):
    p = world.create_entity()
    world.add_component(p, Position(x, y))
    # Make the pellet generous for collision to simplify the test.
    world.add_component(p, Sprite("pellet", 16, 16))
    world.add_component(p, FoodPellet(nutrition=20.0, radius_scale=1.35))
    return p


def _fish_entity(world: World, tank, x: float, y: float):
    e = world.create_entity()
    world.add_component(e, TankRef(tank))
    world.add_component(e, Position(x, y))
    world.add_component(e, Velocity(0.0, 0.0))
    world.add_component(e, Sprite("goldfish", 60, 40))
    world.add_component(e, Brain(state="Idle"))  # start idle; overrides will nudge it
    world.add_component(e, MotionParams(max_speed=300.0, acceleration=4000.0, turn_speed=999.0))
    # Start somewhat hungry so override pushes toward food seeking.
    world.add_component(e, Hunger(hunger=40.0, hunger_rate=0.0, hunger_max=100.0))
    # Use tuning keys actually consumed by our FSM paths
    world.add_component(
        e,
        BehaviorTuning(
            {
                "food_detect_radius": 250.0,
                "food_seek_threshold": 0.80,
                "chase_food_speed_factor": 1.0,
                "eat_extra_margin": 12.0,
                "mouth_radius_factor": 0.40,
                "health_regen_factor": 0.0,
                "health_regen_threshold": 1.0,
                "health_starve_factor": 0.5,
                "noise": 0.0,
            }
        ),
    )
    world.add_component(e, TargetIntent(x, y))
    world.add_component(e, SteeringIntent(0.0, 0.0))
    world.add_component(e, SpeedIntent(desired_speed=0.0))
    return e


def test_chase_and_eat_increases_hunger_and_removes_pellet(make_context, dt):
    world = World()
    ctx: GameContext = make_context()

    tank = _tank(world)
    fish = _fish_entity(world, tank, 100.0, 100.0)

    # Place the pellet well within immediate eat distance:
    # Align the pellet roughly at the fish's nose by centering near sprite center.
    pos = world.get_component(fish, Position)
    spr = world.get_component(fish, Sprite)
    # Put pellet a little to the right of the fish center to be "in front".
    pellet = _pellet_at(world, x=pos.x + spr.base_w * 0.5 + 2.0, y=pos.y + spr.base_h * 0.5)

    behavior = BehaviorSystem(ctx)
    override = StateOverrideSystem()
    transition = StateTransitionSystem(ctx, behavior)
    hunger_sys = HungerSystem()

    before = world.get_component(fish, Hunger).hunger

    # Run a handful of frames:
    #  1) Override should push Idle -> LookForFood (hungry).
    #  2) Behavior should find the nearby pellet -> ChaseFood.
    #  3) ChaseFood should immediately satisfy the eat threshold and destroy the pellet.
