# Resize updates context and tank bounds/position.
from ecs.systems.core.resize_system import ResizeSystem
from ecs.components.core.bounds_component import Bounds
from ecs.components.core.position_component import Position
from ecs.components.core.tank_component import Tank
from world import World

def test_resize_updates_context_and_tank(make_context):
    world = World()
    ctx = make_context()
    # logical tank: 400x300
    ctx.logical_tank_w = 400
    ctx.logical_tank_h = 300

    # one tank entity
    tank = world.create_entity()
    world.add_component(tank, Tank())
    world.add_component(tank, Position(0, 0))
    world.add_component(tank, Bounds(400, 300))

    # request resize to exactly logical size -> scale 1.0
    ctx.needs_resize = True
    ctx.new_screen_w = 400
    ctx.new_screen_h = 300

    sys = ResizeSystem(ctx)
    sys.update(world, dt=0.0)

    b = world.get_component(tank, Bounds)
    p = world.get_component(tank, Position)
    assert (b.width, b.height) == (400, 300)
    assert (p.x, p.y) == (0, 0)
    assert abs(ctx.tank_scale - 1.0) < 1e-6
