"""
ecs/factories/fish_factory.py

Factory helpers for creating fish entities with sensible, slightly
personalized (jittered) stats and behavior tuning.

Notes
-----
- Numeric stats are jittered for variety:
  * "stable" keys get ±4% noise
  * everything else gets ±10% noise
- Species-provided "behavior" overrides are merged on top of defaults.
- This factory assumes `species_data` includes at least:
    - width (int), height (int), max_age (float/int)
    - sprite (optional; falls back to species_id)
"""

from __future__ import annotations

import random
from typing import Any, Dict

from ecs.components.core.position_component import Position
from ecs.components.core.sprite_component import Sprite
from ecs.components.core.tank_ref_component import TankRef
from ecs.components.fish.motion_component import MotionParams
from ecs.components.core.velocity_component import Velocity
from ecs.components.fish.brain_component import Brain
from ecs.components.core.collider_component import Collider
from ecs.components.fish.age_component import Age
from ecs.components.fish.hunger_component import Hunger
from ecs.components.fish.health_component import Health
from ecs.components.fish.species_component import Species
from ecs.components.fish.behavior_tuning import BehaviorTuning
from ecs.components.fish.target_intent_component import TargetIntent
from ecs.components.fish.steering_intent_component import SteeringIntent
from ecs.components.fish.speed_intent_component import SpeedIntent
from ecs.components.fish.breeding_component import Breeding


# Keys that should vary less to keep movement feel consistent across runs.
_STABILITY_KEYS = {"speed", "acceleration", "turn_speed", "hunger_rate"}


def _jitter(value: Any, key: str) -> Any:
    """
    Return a jittered copy of numeric values; non-numerics are returned as-is.

    Stable keys get a small ±4% noise. All other numeric keys get ±10%.
    """
    if not isinstance(value, (int, float)):
        return value

    if key in _STABILITY_KEYS:
        span = 0.04
    else:
        span = 0.10

    return value * (1.0 + random.uniform(-span, span))


def create_fish(
    world,
    context,
    tank_entity: int,
    species_id: str,
    species_data: Dict[str, Any],
    x: float,
    y: float,
) -> int:
    """
    Create a fish entity with components and jittered stats.

    Parameters
    ----------
    world : World
        ECS world to mutate.
    context : GameContext
        Provides global defaults and configs (fish_defaults, etc.).
    tank_entity : int
        Entity id of the tank this fish belongs to.
    species_id : str
        Key/name of the species (used as fallback sprite id and display name).
    species_data : dict
        Species record (expects width, height, max_age, optional sprite, behavior).
    x, y : float
        Initial logical coordinates inside the tank.

    Returns
    -------
    int
        The newly created entity id.
    """
    # ---- Required species fields (fail fast with a clear error) -----------------
    try:
        base_w = int(species_data["width"])
        base_h = int(species_data["height"])
        max_age = float(species_data["max_age"])
    except KeyError as exc:
        missing = str(exc).strip("'")
        raise KeyError(
            f"species_data missing required key '{missing}' for species '{species_id}'"
        ) from exc

    # ---- Merge stats: defaults <- species_data (flat) ---------------------------
    # Start with global defaults, let species override them.
    defaults: Dict[str, Any] = (context.fish_defaults or {}).copy()
    merged_stats: Dict[str, Any] = defaults.copy()
    merged_stats.update(species_data)

    # ---- Merge behavior: start from the flattened stats-overrides --------------
    # We copy any keys that exist in defaults (to inherit global behavior fields),
    # then override with explicit species["behavior"] block if provided.
    species_behavior: Dict[str, Any] = species_data.get("behavior", {}) or {}
    merged_behavior: Dict[str, Any] = {
        k: merged_stats[k] for k in defaults.keys() if k in merged_stats
    }
    merged_behavior.update(species_behavior)

    # ---- Apply jitter for personal variation -----------------------------------
    merged_stats = {k: _jitter(v, k) for k, v in merged_stats.items()}
    merged_behavior = {k: _jitter(v, k) for k, v in merged_behavior.items()}

    # ---- Entity + core components ----------------------------------------------
    e = world.create_entity()

    world.add_component(e, TankRef(tank_entity))
    world.add_component(e, Position(x, y))

    sprite_name = species_data.get("sprite", species_id)
    world.add_component(
        e,
        Sprite(
            image_id=sprite_name,
            base_w=base_w,
            base_h=base_h,
            faces_right=bool(species_data.get("sprite_faces_right", True)),
        ),
    )

    world.add_component(
        e,
        MotionParams(
            max_speed=float(merged_stats["speed"]),
            acceleration=float(merged_stats["acceleration"]),
            turn_speed=float(merged_stats["turn_speed"]),
            dart_multiplier=float(merged_stats["dart_multiplier"]),
        ),
    )

    world.add_component(e, Velocity(0.0, 0.0))

    # Collider radius heuristic: ~40% of width tends to look reasonable.
    world.add_component(e, Collider(radius=base_w * 0.4))

    world.add_component(e, Age(age=0.0, lifespan=max_age))

    world.add_component(
        e,
        Hunger(
            hunger=float(merged_stats["hunger_max"]),
            hunger_rate=float(merged_stats["hunger_rate"]),
            hunger_max=float(merged_stats["hunger_max"]),
        ),
    )

    world.add_component(
        e,
        Health(
            value=float(merged_stats["health_max"]),
            max_value=float(merged_stats["health_max"]),
        ),
    )

    world.add_component(
        e,
        Species(
            species_id=species_id,
            display_name=species_id.title(),
            base_speed=float(merged_stats["speed"]),
        ),
    )
    world.add_component(e, Breeding())

    # Brain + behavior tuning
    brain = Brain(state="Cruise")
    world.add_component(e, brain)
    world.add_component(e, BehaviorTuning(merged_behavior))

    # Intent components (targets, steering and speed requests)
    world.add_component(e, TargetIntent())
    world.add_component(e, SteeringIntent())
    world.add_component(e, SpeedIntent())

    return e
