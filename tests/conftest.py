# tests/conftest.py
# pytest shared fixtures: headless pygame, deterministic RNG, and handy builders.
import os
import random
import pytest

# Headless drivers must be set before importing pygame
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from world import World
from game_context import GameContext

# Core components we’ll reuse in fixtures
from ecs.components.core.position_component import Position
from ecs.components.core.bounds_component import Bounds
from ecs.components.core.tank_component import Tank
from ecs.components.core.tank_ref_component import TankRef
from ecs.components.core.sprite_component import Sprite
from ecs.components.core.velocity_component import Velocity
from ecs.components.fish.motion_component import MotionParams
from ecs.components.fish.target_intent_component import TargetIntent
from ecs.components.fish.steering_intent_component import SteeringIntent
from ecs.components.fish.speed_intent_component import SpeedIntent
from ecs.components.fish.brain_component import Brain
from ecs.components.fish.behavior_tuning import BehaviorTuning
from ecs.components.fish.species_component import Species
from ecs.components.fish.age_component import Age
from ecs.components.fish.hunger_component import Hunger
from ecs.components.fish.health_component import Health

@pytest.fixture(scope="session", autouse=True)
def _pygame_bootstrap():
    """Initialize pygame + font + a tiny video mode once for the whole suite."""
    pygame.init()                 # includes font.init()
    pygame.font.init()
    pygame.display.init()
    pygame.display.set_mode((1, 1))
    try:
        yield
    finally:
        # single, orderly shutdown at end of session
        pygame.display.quit()
        pygame.font.quit()
        pygame.quit()

@pytest.fixture(autouse=True)
def _deterministic_random_seed():
    random.seed(1337)

@pytest.fixture
def dt():
    return 0.016  # ~60 FPS

@pytest.fixture
def make_context():
    """Construct a GameContext and allow overrides for logical tank sizing, etc."""
    def _mk(**overrides):
        ctx = GameContext()
        if "logical_w" in overrides:
            ctx.logical_tank_w = int(overrides["logical_w"])
        if "logical_h" in overrides:
            ctx.logical_tank_h = int(overrides["logical_h"])
        for k, v in overrides.items():
            setattr(ctx, k, v)
        return ctx
    return _mk

@pytest.fixture
def make_world():
    return lambda: World()

@pytest.fixture
def make_tank():
    def _mk(world, x=0, y=0, w=600, h=400):
        e = world.create_entity()
        world.add_component(e, Tank())
        world.add_component(e, Position(x, y))
        world.add_component(e, Bounds(w, h))
        return e
    return _mk

@pytest.fixture
def make_dummy_fish(make_tank):
    """
    Create a fish entity with the components your systems expect.
    Adds a TankRef so render/behavior math that needs a tank still works.
    """
    def _mk(world, x=100, y=200, max_speed=150.0, species="goldfish"):
        tank = make_tank(world, x=0, y=0, w=800, h=600)
        e = world.create_entity()
        world.add_component(e, TankRef(tank))
        world.add_component(e, Position(x, y))
        world.add_component(e, Sprite(image_id=species, base_w=60, base_h=40))
        world.add_component(e, Velocity(0.0, 0.0))
        world.add_component(e, MotionParams(max_speed=max_speed, acceleration=200.0, turn_speed=8.0))
        world.add_component(e, TargetIntent(x, y))
        world.add_component(e, SpeedIntent(0.0))
        world.add_component(e, SteeringIntent())
        world.add_component(e, Brain(state="Cruise"))
        world.add_component(e, BehaviorTuning({
            "cruise_min_time": 0.2,
            "cruise_max_time": 0.3,
            "cruise_arrival_radius": 40.0,
            "cruise_speed_factor": 0.6,
            "transition_to_idle_chance": 0.0,
            "idle_min_time": 0.1,
            "idle_max_time": 0.2,
            "idle_speed_factor": 0.05,
            "idle_bob_amplitude": 20.0,
            "idle_bob_frequency": 1.0,
            "transition_to_cruise_chance": 0.02,
            "food_detect_radius": 250.0,
            "food_seek_threshold": 0.80,
            "look_for_food_speed_factor": 1.0,
            "chase_food_speed_factor": 1.00,
            "food_nutrition": 40.0,
            "noise": 0.0,
            "mouth_radius_factor": 0.40,
            "eat_extra_margin": 8.0,
        }))
        world.add_component(e, Species(species_id=species, display_name=species.title(), base_speed=max_speed))
        world.add_component(e, Age(age=0.0, lifespan=5.0, stage="Adult", pre_hatch=0.0))
        world.add_component(e, Hunger(hunger=50.0, hunger_rate=1.0, hunger_max=100.0))
        world.add_component(e, Health(value=100.0, max_value=100.0))
        return e
    return _mk
