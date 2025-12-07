# ecs/fsm/dead_state.py
from ecs.fsm.base_state import BaseState
from ecs.components.tags.affected_by_gravity import AffectedByGravity

class DeadState(BaseState):
    NAME = "Dead"

    def enter(self, fish, context):
        brain = fish.brain
        brain.current_desired_speed = 0.0
        # Sink via gravity system instead of manual per-frame motion
        sink = float(context.balancing.get("dead_sink_speed", 30.0))
        # Add/update gravity component
        # (The system will handle resting on sand.)
        fish_entity = getattr(fish, "entity_id", None)
        world = getattr(fish, "world", None)
        # fish_view doesn’t keep entity/world by default; set via systems that call enter().
        # Safer approach: attach directly on known components via world if available.
        if world is not None and fish_entity is not None:
            world.add_component(fish_entity, AffectedByGravity(speed=sink))
        else:
            # Fallback: try to mutate through the view if it exposes world/add (some setups do)
            try:
                fish.add_component(AffectedByGravity(speed=sink))  # type: ignore[attr-defined]
            except Exception:
                pass

    def update(self, fish, speed_intent, context, dt, world):
        # Dead fish do not self-propel.
        speed_intent.desired_speed = 0.0
        # No manual sinking here; GravitySystem handles it.
        return None
