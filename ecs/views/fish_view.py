from dataclasses import dataclass
from typing import Optional
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
@dataclass
class FishView:
    brain: Brain
    pos: Position
    vel: Optional[Velocity]
    motion: MotionParams
    hunger: Hunger
    sprite: Sprite
    tuning: BehaviorTuning
    target: TargetIntent
    steering: SteeringIntent
    speed: SpeedIntent