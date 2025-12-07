import math

from world import World
from game_context import GameContext

from ecs.components.core.position_component import Position
from ecs.components.core.velocity_component import Velocity
from ecs.components.core.sprite_component import Sprite
from ecs.components.core.tank_ref_component import TankRef

from ecs.systems.core.avoidance_system import AvoidanceSystem
from ecs.components.fish.steering_intent_component import SteeringIntent


def _add_tank(world: World, w: int, h: int):
    e = world.create_entity()
    # Many systems just need TankRef to exist on entities plus logical size in context.
    return e


def _make_fish_at(world: World, tank, x, y, w=40, h=20):
    e = world.create_entity()
    world.add_component(e, TankRef(tank))
    world.add_component(e, Position(x, y))
    world.add_component(e, Sprite("goldfish", w, h))
    world.add_component(e, Velocity(0.0, 0.0))
    # AvoidanceSystem writes into SteeringIntent; ensure it exists
    world.add_component(e, SteeringIntent())
    return e


def test_wall_bounce_and_clamp(make_context):
    world = World()
    ctx: GameContext = make_context(logical_w=200, logical_h=100)
    ctx.logical_tank_w = 200
    ctx.logical_tank_h = 100
    tank = _add_tank(world, 200, 100)

    fish = _make_fish_at(world, tank, x=1, y=50, w=10, h=10)
    vel = world.get_component(fish, Velocity)
    vel.vx = -30.0  # aiming out of bounds

    sys = AvoidanceSystem(ctx)
    # Single update should push intent to the right
    sys.update(world, dt=0.016)

    intent = world.get_component(fish, SteeringIntent)
    assert intent.dx >= 0.0  # bounced / clamped to non-left


def test_avoidance_pushes_away_from_wall(make_context):
    world = World()
    ctx: GameContext = make_context(logical_w=200, logical_h=100)
    ctx.logical_tank_w = 200
    ctx.logical_tank_h = 100
    tank = _add_tank(world, 200, 100)

    fish = _make_fish_at(world, tank, x=5, y=50, w=10, h=10)
    pos0 = world.get_component(fish, Position).x
    # give it some left-ward velocity so avoidance has something to scale with
    vel = world.get_component(fish, Velocity)
    vel.vx = -20.0
    vel.vy = 0.0

    sys = AvoidanceSystem(ctx)
    for _ in range(15):
        sys.update(world, dt=0.016)
        # Movement system would normally integrate; nudge position manually so we can observe change
        intent = world.get_component(fish, SteeringIntent)
        world.get_component(fish, Position).x += max(0.0, intent.dx) * 2.0  # crude push right

    assert world.get_component(fish, Position).x > pos0
