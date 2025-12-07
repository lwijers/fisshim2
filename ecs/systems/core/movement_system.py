from math import hypot, atan2, cos, sin
import random
from ecs.components.fish.motion_component import MotionParams
from ecs.components.core.position_component import Position
from ecs.components.core.tank_ref_component import TankRef
from ecs.components.core.velocity_component import Velocity
from ecs.components.fish.behavior_tuning import BehaviorTuning
from ecs.components.core.sprite_component import Sprite
from ecs.components.tags.dead_component import DeadFlag
from ecs.components.fish.target_intent_component import TargetIntent
from ecs.components.fish.steering_intent_component import SteeringIntent
from ecs.components.fish.speed_intent_component import SpeedIntent

def _clamp_angle(delta, limit):
    if delta > limit: return limit
    if delta < -limit: return -limit
    return delta

class MovementSystem:
    """
    Integrates desired motion:
      - Builds direction from target + steering (AvoidanceSystem)
      - Applies turning limit and acceleration clamp
      - Applies damping
      - Integrates pos/vel
    NOTE: No boundary checks or bounce here — CollisionSystem handles that.
    """
    def __init__(self, context):
        self.context = context
        b = context.balancing
        self.damping = float(b.get("movement_damping", 0.94))

    def update(self, world, dt: float):
        for e in world.entities_with(
            Position, Velocity, MotionParams,
            TargetIntent, SteeringIntent, SpeedIntent, TankRef, Sprite
        ):
            if world.get_component(e, DeadFlag):
                continue

            pos = world.get_component(e, Position)
            vel = world.get_component(e, Velocity)
            motion = world.get_component(e, MotionParams)
            target = world.get_component(e, TargetIntent)
            steer  = world.get_component(e, SteeringIntent)
            speedi = world.get_component(e, SpeedIntent)
            spr    = world.get_component(e, Sprite)

            # Direction toward target + soft steering (already set by AvoidanceSystem)
            dx = target.tx - pos.x; dy = target.ty - pos.y
            dist = max(1e-6, hypot(dx, dy))
            base_dx, base_dy = dx / dist, dy / dist
            dir_x = base_dx + steer.dx; dir_y = base_dy + steer.dy

            # Optional behavioral noise
            tuning = world.get_component(e, BehaviorTuning)
            if tuning:
                noise = float(tuning.get("noise", 0.0))
                if noise > 0.0:
                    dir_x += random.uniform(-noise, noise)
                    dir_y += random.uniform(-noise, noise)

            # Normalize final dir
            dlen = hypot(dir_x, dir_y)
            if dlen > 1e-5:
                dir_x /= dlen; dir_y /= dlen

            # Speed target
            desired_speed = max(0.0, min(speedi.desired_speed, motion.max_speed))
            des_vx, des_vy = dir_x * desired_speed, dir_y * desired_speed

            # Heading turn limit
            cur_speed = hypot(vel.dx, vel.dy)
            if cur_speed < 1e-6:
                heading_vx, heading_vy = dir_x, dir_y
            else:
                cur_ang = atan2(vel.dy, vel.dx)
                des_ang = atan2(des_vy, des_vx) if desired_speed > 1e-6 else cur_ang
                da = (des_ang - cur_ang + 3.14159265) % (2*3.14159265) - 3.14159265
                max_rotate = max(0.0, motion.turn_speed) * dt
                cur_ang += _clamp_angle(da, max_rotate)
                heading_vx, heading_vy = cos(cur_ang), sin(cur_ang)

            # Accel clamp toward target velocity
            target_vx, target_vy = heading_vx * desired_speed, heading_vy * desired_speed
            dvx, dvy = target_vx - vel.dx, target_vy - vel.dy
            dv_len = hypot(dvx, dvy); max_delta = motion.acceleration * dt
            if dv_len > max_delta and dv_len > 1e-6:
                s = max_delta / dv_len; dvx *= s; dvy *= s

            # Apply velocity & damping
            vel.dx = (vel.dx + dvx) * self.damping
            vel.dy = (vel.dy + dvy) * self.damping

            # Integrate position (no clamping here)
            pos.x += vel.dx * dt
            pos.y += vel.dy * dt

            # Reset steering each frame
            steer.dx = 0.0; steer.dy = 0.0
