# ecs/systems/behavior_system.py
"""
BehaviorSystem
--------------
Bridges ECS components into a lightweight `FishView` and drives the per-fish FSM.

Responsibilities
* Build (and reuse) a FishView for each entity that has the full set of required
  components for behavior.
* Call `enter()` the first frame an entity is observed in a given state.
* Call `update()` on the current state's handler to produce a *proposed* next state.
* Return a mapping {entity_id: next_state_name or None} for the transition system.

Notes
* This system does not mutate Brain.state directly — it only proposes transitions.
* A small cache of FishView objects avoids reallocations each frame.
"""

from __future__ import annotations

from typing import Dict, Optional, Tuple

from ecs.views.fish_view import FishView
from ecs.fsm import FSM_STATES
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
from ecs.components.core.tank_ref_component import TankRef


class BehaviorSystem:
    """
    Orchestrates FSM updates for all fish entities that have the required components.
    """

    # Components required for a fish to participate in behavior updates.
    _REQUIRED = (
        Brain, Position, MotionParams, Velocity, Hunger,
        BehaviorTuning, Sprite, TankRef, TargetIntent, SteeringIntent, SpeedIntent,
    )

    def __init__(self, context) -> None:
        self.context = context

        # entity_id -> FishView (reused/updated each frame)
        self._views: Dict[int, FishView] = {}

        # Tracks whether we've called enter() for (entity, state_name).
        # Using a set is slightly cheaper than a dict of booleans.
        self._entered: Dict[Tuple[int, str], bool] = {}

        # Cache FSM registry reference (micro-optimization on dict global).
        self._fsm = FSM_STATES

    # --------------------------------------------------------------------- #
    # Internal helpers
    # --------------------------------------------------------------------- #

    def _get_view(
        self,
        e: int,
        brain: Brain,
        pos: Position,
        vel: Velocity,
        motion: MotionParams,
        hunger: Hunger,
        sprite: Sprite,
        tuning: BehaviorTuning,
        target: TargetIntent,
        steering: SteeringIntent,
        speed: SpeedIntent,
    ) -> FishView:
        """
        Return a cached FishView for the entity, updating its references in-place.
        """
        view = self._views.get(e)
        if view is None:
            view = FishView(brain, pos, vel, motion, hunger, sprite, tuning, target, steering, speed)
            self._views[e] = view
            return view

        # Refresh references (no new allocations).
        view.brain = brain
        view.pos = pos
        view.vel = vel
        view.motion = motion
        view.hunger = hunger
        view.sprite = sprite
        view.tuning = tuning
        view.target = target
        view.steering = steering
        view.speed = speed
        return view

    def _ensure_enter_called(self, e: int, brain: Brain, view: FishView) -> None:
        """
        Call enter() exactly once per (entity, state_name).
        """
        key = (e, brain.state)
        if key not in self._entered:
            self._fsm[brain.state].enter(view, self.context)
            self._entered[key] = True

    # --------------------------------------------------------------------- #
    # ECS system API
    # --------------------------------------------------------------------- #

    def update(self, world, dt: float) -> Dict[int, Optional[str]]:
        """
        Build FishViews, ensure state `enter()` is called, then invoke the state's
        `update()` to compute proposed next states.

        Returns
        -------
        Dict[entity_id, next_state or None]
        """
        proposed: Dict[int, Optional[str]] = {}
        fsm = self._fsm  # local ref

        # Iterate only over entities that have all required components.
        for e in world.entities_with(*self._REQUIRED):
            # Pull components once each (local vars are faster & clearer).
            brain: Brain = world.get_component(e, Brain)
            pos: Position = world.get_component(e, Position)
            vel: Velocity = world.get_component(e, Velocity)
            motion: MotionParams = world.get_component(e, MotionParams)
            hunger: Hunger = world.get_component(e, Hunger)
            sprite: Sprite = world.get_component(e, Sprite)
            tuning: BehaviorTuning = world.get_component(e, BehaviorTuning)
            target: TargetIntent = world.get_component(e, TargetIntent)
            steer: SteeringIntent = world.get_component(e, SteeringIntent)
            speed: SpeedIntent = world.get_component(e, SpeedIntent)

            # Compose (or refresh) the lightweight view.
            view = self._get_view(e, brain, pos, vel, motion, hunger, sprite, tuning, target, steer, speed)

            # Make entity/world available to state handlers (e.g., DeadState.enter)
            setattr(view, "entity_id", e)
            setattr(view, "world", world)

            # Ensure we called enter() for the current state at least once.
            self._ensure_enter_called(e, brain, view)

            # Run the state's update; it may return a next-state string or None.
            next_state = fsm[brain.state].update(view, speed, self.context, dt, world)
            proposed[e] = next_state

        return proposed
