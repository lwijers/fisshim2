# Core ECS world behaviors: creation, indexing, queries, destruction.
from world import World
from ecs.components.core.position_component import Position
from ecs.components.core.velocity_component import Velocity

def test_entities_with_intersection():
    world = World()
    e1 = world.create_entity(); world.add_component(e1, Position(1, 2))
    e2 = world.create_entity(); world.add_component(e2, Position(3, 4)); world.add_component(e2, Velocity(0, 0))
    e3 = world.create_entity(); world.add_component(e3, Velocity(0, 0))
    only_pos = set(world.entities_with(Position))
    both = set(world.entities_with(Position, Velocity))
    only_vel = set(world.entities_with(Velocity))
    assert e1 in only_pos and e2 in only_pos and e3 not in only_pos
    assert e2 in both and e1 not in both and e3 not in both
    assert e2 in only_vel and e3 in only_vel and e1 not in only_vel

def test_destroy_entity_cleans_indices():
    world = World()
    e = world.create_entity()
    world.add_component(e, Position(10, 20))
    world.add_component(e, Velocity(1, 2))
    assert e in set(world.entities_with(Position, Velocity))
    world.destroy_entity(e)
    assert e not in world.entities
    assert e not in set(world.entities_with(Position))
    assert e not in set(world.entities_with(Velocity))
