from math import hypot
from ecs.components.core.position_component import Position
from ecs.components.core.velocity_component import Velocity
from ecs.components.core.tank_ref_component import TankRef
from ecs.components.fish.steering_intent_component import SteeringIntent
from math import hypot

from ecs.components.core.position_component import Position
from ecs.components.core.velocity_component import Velocity
from ecs.components.core.tank_ref_component import TankRef
from ecs.components.fish.steering_intent_component import SteeringIntent


class AvoidanceSystem:
    def __init__(self, context):
        self.context = context
        b = context.balancing or {}
        # Width of the "avoid bands" hugging the walls (in logical px).
        self.margin = float(b.get("avoidance_margin", 20.0))
        # Max magnitude we allow for the avoidance steering contribution.
        self.max_strength = float(b.get("avoidance_max_strength", 0.25))
        # Reference speed used to scale avoidance with current speed.
        self._speed_ref = float(b.get("typical_max_speed", 40.0))

    def update(self, world, dt):
        # Logical tank size
        w = float(self.context.logical_tank_w)
        h = float(self.context.logical_tank_h)
        m = float(self.margin)

        # Where the *swimmable* water ends at the bottom.
        # This is the top edge of the dark brown frame in the background.
        swim_bottom_margin = float(getattr(self.context, "swim_bottom_margin", 64.0))
        water_bottom = h - swim_bottom_margin  # y coordinate in logical space

        for e in world.entities_with(Position, SteeringIntent, TankRef, Velocity):
            pos: Position = world.get_component(e, Position)
            intent: SteeringIntent = world.get_component(e, SteeringIntent)
            vel: Velocity = world.get_component(e, Velocity)

            # Normalize velocity to get a directional bias; if nearly stopped,
            # avoidance is minimal.
            speed = hypot(vel.dx, vel.dy)
            if speed < 1e-3:
                continue
            vx = vel.dx / speed
            vy = vel.dy / speed

            ax = 0.0  # avoidance steering x
            ay = 0.0  # avoidance steering y

            # ---- Left wall band ----
            if pos.x < m:
                # Push to the right; strength grows as we get closer to 0.
                # Use max(0, -vx) so we push more when currently heading *into* the wall.
                ax += (1.0 - (pos.x / m)) * max(0.0, -vx)

            # ---- Right wall band ----
            if pos.x > w - m:
                # Push to the left; strength grows as we get closer to w.
                ax -= (1.0 - ((w - pos.x) / m)) * max(0.0, vx)

            # ---- Top wall band ----
            if pos.y < m:
                # Push downward.
                ay += (1.0 - (pos.y / m)) * max(0.0, -vy)

            # ---- Bottom swim floor band (NOT the tank bottom) ----
            # Keep fish above the water_bottom line (top of dark brown frame).
            if pos.y > water_bottom - m:
                # Push upward; strength grows as we approach water_bottom.
                # Use the current downward component (vy>0) to bias more when heading down.
                ay -= (1.0 - ((water_bottom - pos.y) / m)) * max(0.0, vy)

            # Scale avoidance with speed so gentle drifters don’t overreact,
            # and sprinters get stronger correction.
            speed_scale = min(1.0, speed / self._speed_ref)
            ax *= speed_scale
            ay *= speed_scale

            # Clamp vector to the configured maximum strength.
            strength = hypot(ax, ay)
            if strength > self.max_strength and strength > 1e-7:
                s = self.max_strength / strength
                ax *= s
                ay *= s

            # Accumulate into the per-fish steering intent (MovementSystem will consume it).
            intent.dx += ax
            intent.dy += ay