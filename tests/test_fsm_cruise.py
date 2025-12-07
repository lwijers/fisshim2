# Deterministic cruise timing => Idle after max time.
from world import World
from ecs.fsm.cruise_state import CruiseState
from ecs.views.fish_view import FishView
from ecs.components.fish.brain_component import Brain
from ecs.components.core.position_component import Position
from ecs.components.core.velocity_component import Velocity
from ecs.components.fish.motion_component import MotionParams
from ecs.components.fish.hunger_component import Hunger
from ecs.components.core.sprite_component import Sprite
from ecs.components.fish.behavior_tuning import BehaviorTuning
from ecs.components.fish.target_intent_component import TargetIntent
from ecs.components.fish.steering_intent_component import SteeringIntent
from ecs.components.fish.speed_intent_component import SpeedIntent

def _make_view():
    brain = Brain(state="Cruise")
    pos = Position(0, 0)
    vel = Velocity(0.0, 0.0)
    motion = MotionParams(max_speed=100.0, acceleration=200.0, turn_speed=8.0)
    hunger = Hunger(hunger=50.0, hunger_rate=0.0, hunger_max=100.0)
    sprite = Sprite("goldfish", 60, 40)
    tuning = BehaviorTuning({
        "cruise_min_time": 0.05,
        "cruise_max_time": 0.06,
        "cruise_arrival_radius": 2.0,
        "cruise_speed_factor": 0.2,
        "transition_to_idle_chance": 0.0,
    })
    target = TargetIntent(0.0, 0.0)
    steer = SteeringIntent()
    speed = SpeedIntent(0.0)
    return FishView(brain, pos, vel, motion, hunger, sprite, tuning, target, steer, speed), speed

def test_cruise_transitions_to_idle_after_max_time(make_context, dt):
    world = World(); ctx = make_context()
    view, speed = _make_view()
    state = CruiseState()
    state.enter(view, ctx)
    result = None
    for _ in range(30):  # ~0.48 s
        result = state.update(view, speed, ctx, dt, world)
        if result:
            break
    assert result == "Idle"
    assert view.brain.state == "Cruise"  # state machine proposes; transition system would switch
