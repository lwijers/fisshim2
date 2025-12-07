from math import hypot

from world import World
from game_context import GameContext

from ecs.components.core.position_component import Position
from ecs.components.core.velocity_component import Velocity
from ecs.components.core.sprite_component import Sprite
from ecs.components.core.tank_component import Tank
from ecs.components.core.tank_ref_component import TankRef

from ecs.components.fish.motion_component import MotionParams
from ecs.components.fish.target_intent_component import TargetIntent
from ecs.components.fish.steering_intent_component import SteeringIntent
from ecs.components.fish.speed_intent_component import SpeedIntent

from ecs.systems.core.movement_system import MovementSystem


def test_movement_updates_position(make_world, make_context, make_tank):
    world: World = make_world()
    context: GameContext = make_context()

    # Tank (MovementSystem requires TankRef on fish)
    tank = make_tank(world, x=0, y=0, w=800, h=600)

    # Minimal fish with the components MovementSystem expects
    e = world.create_entity()
    world.add_component(e, TankRef(tank))
    world.add_component(e, Position(100.0, 100.0))
    world.add_component(e, Velocity(10.0, 5.0))
    world.add_component(e, Sprite("goldfish", base_w=60, base_h=40))
    world.add_component(e, MotionParams(max_speed=1000.0, acceleration=10000.0, turn_speed=999.0))

    # Point the target roughly along the current velocity direction
    pos = world.get_component(e, Position)
    vel = world.get_component(e, Velocity)
    speed_mag = hypot(vel.dx, vel.dy)
    world.add_component(e, TargetIntent(pos.x + vel.dx * 10.0, pos.y + vel.dy * 10.0))
    world.add_component(e, SteeringIntent(0.0, 0.0))
    world.add_component(e, SpeedIntent(desired_speed=speed_mag))

    MovementSystem(context).update(world, dt=1.0)

    pos_after = world.get_component(e, Position)
    assert pos_after.x > 100.0
    assert pos_after.y > 100.0


def test_hysteresis_facing_stability():
    """
    Only assert obvious left/right flips (far from deadzone).
    """
    from ecs.systems.renderers.draw_sprite import choose_facing

    spr = Sprite("goldfish", base_w=60, base_h=40)
    pos = Position(50, 50)

    # Far right -> should face right
    target = TargetIntent(300, 50)
    face_right, _ = choose_facing(spr, Velocity(0.0, 0.0), target, pos, False)
    assert face_right is True

    # Far left -> should face left
    target = TargetIntent(-300, 50)
    face_right, _ = choose_facing(spr, Velocity(0.0, 0.0), target, pos, True)
    assert face_right is False
