from __future__ import annotations
from typing import List, Tuple, Optional
import random

from ecs.components.core.position_component import Position
from ecs.components.core.sprite_component import Sprite
from ecs.components.core.tank_ref_component import TankRef
from ecs.components.tags.food_pellet_component import FoodPellet
from ecs.components.tags.affected_by_gravity import AffectedByGravity
from ecs.components.fish.age_component import Age
from ecs.components.fish.brain_component import Brain
from ecs.components.core.velocity_component import Velocity

class PlacementSystem:
    """
    Receives screen-space clicks (via enqueue_click) and spawns pellets or eggs
    based on the current tool state in context.

    MouseSystem calls:
        placement.enqueue_click(x, y)

    This system then processes them during update(...) so spawns happen the same
    frame (after UI handling).

    Also exposes `spawn_egg_at(world, x_logical, y_logical, species_id=None)` so
    gameplay systems (breeding) can spawn “the same egg” as the EGG tool.
    """

    def __init__(self, context):
        self.context = context
        self._tank_entity: Optional[int] = None
        self._pending_clicks: List[Tuple[int, int]] = []

    def set_tank(self, tank_entity: int) -> None:
        self._tank_entity = tank_entity

    def enqueue_click(self, x: int, y: int) -> None:
        self._pending_clicks.append((int(x), int(y)))

    # -------------------- helpers --------------------
    def _point_in_tank_screen(self, x: int, y: int) -> bool:
        sx = int(getattr(self.context, "tank_screen_x", 0))
        sy = int(getattr(self.context, "tank_screen_y", 0))
        sw = int(getattr(self.context, "tank_screen_w", 0))
        sh = int(getattr(self.context, "tank_screen_h", 0))
        return (sx <= x <= sx + sw) and (sy <= y <= sy + sh)

    def _spawn_pellet(self, world, x: int, y: int) -> None:
        if self._tank_entity is None:
            return
        scale = float(getattr(self.context, "tank_scale", 1.0) or 1.0)
        sx = int(getattr(self.context, "tank_screen_x", 0))
        sy = int(getattr(self.context, "tank_screen_y", 0))
        sw = int(getattr(self.context, "tank_screen_w", 0))
        sh = int(getattr(self.context, "tank_screen_h", 0))
        if not (sx <= x <= sx + sw and sy <= y <= sy + sh):
            return

        cfg = self.context.pellets or {}
        image_id = cfg.get("sprite", "pellet")
        w = int(cfg.get("width", 16))
        h = int(cfg.get("height", 16))
        nutrition = float(cfg.get("nutrition", 40.0))
        radius_scale = float(cfg.get("radius_scale", 1.0))
        off_x = float(cfg.get("center_offset_x", 0.0))
        off_y = float(cfg.get("center_offset_y", 0.0))
        fall_speed = float(cfg.get("fall_speed", 60.0))

        logical_x = (x - sx) / scale
        logical_y = (y - sy) / scale

        e = world.create_entity()
        world.add_component(e, TankRef(self._tank_entity))
        world.add_component(e, Position(logical_x, logical_y))
        world.add_component(e, Sprite(image_id=image_id, base_w=w, base_h=h))
        world.add_component(e, FoodPellet(nutrition=nutrition, radius_scale=radius_scale,
                                          center_off_x=off_x, center_off_y=off_y))
        world.add_component(e, AffectedByGravity(speed=fall_speed))

        audio = getattr(self.context, "audio", None)
        if audio:
            audio.play("pellet_drop")

    # -------------------- SPAWN EGG (click) --------------------
    def _spawn_egg(self, world, click_x: int, click_y: int) -> None:
        """Same as before, but routed through spawn_egg_at for single source of truth."""
        if not getattr(self.context, "egging_enabled", False):
            return
        if self._tank_entity is None:
            return

        scale = float(getattr(self.context, "tank_scale", 1.0))
        tank_pos = world.get_component(self._tank_entity, Position)
        if tank_pos is None or scale <= 0.0:
            return

        sx, sy = tank_pos.x, tank_pos.y
        sw = int(getattr(self.context, "tank_screen_w", 0))
        sh = int(getattr(self.context, "tank_screen_h", 0))
        if not (sx <= click_x <= sx + sw and sy <= click_y <= sy + sh):
            return

        logical_x = (click_x - sx) / scale
        logical_y = 0.0  # eggs fall from the top (tool behavior)
        # Delegate to shared path (random species like the tool normally does)
        self.spawn_egg_at(world, logical_x, logical_y, species_id=None)

    # -------------------- SPAWN EGG (programmatic) --------------------
    def spawn_egg_at(self, world, x_logical: float, y_logical: float, species_id: Optional[str] = None) -> None:
        """
        Programmatic logical egg spawn used by CourtshipSystem and others.
        This mirrors the EGG tool path: create a full fish via factory, then
        force Egg stage + gravity so all downstream systems (aging, UI) see it.
        """
        if self._tank_entity is None:
            return

        # Choose species (given or random from config)
        species_map = getattr(self.context, "species_config", {}) or {}
        if not species_map:
            return
        if species_id is None:
            species_id = random.choice(list(species_map.keys()))
        sdata = species_map.get(species_id)
        if not sdata:
            return

        from ecs.factories.fish_factory import create_fish
        e = create_fish(world, self.context, self._tank_entity, species_id, sdata, float(x_logical), float(y_logical))

        # Force Egg stage visuals/physics (WHY: ensure same as the tool; keeps window + aging consistent)
        age = world.get_component(e, Age)
        if age:
            age.stage = "Egg"
            age.age = 0.0
            age.pre_hatch = 0.0

        brain = world.get_component(e, Brain)
        if brain:
            brain.state = "Egg"
            brain.current_desired_speed = 0.0

        vel = world.get_component(e, Velocity)
        if vel:
            vel.dx = 0.0
            vel.dy = 0.0

        if world.get_component(e, AffectedByGravity) is None:
            fall_speed = float((getattr(self.context, "balancing", {}) or {}).get("egg_fall_speed", 55.0))
            world.add_component(e, AffectedByGravity(speed=fall_speed))

        audio = getattr(self.context, "audio", None)
        if audio:
            audio.play("pellet_drop")

    # -------------------- ECS entry --------------------
    def update(self, world, dt: float) -> None:
        if not self._pending_clicks:
            return

        # Process in FIFO order; each click spawns either egg or pellet.
        while self._pending_clicks:
            click_x, click_y = self._pending_clicks.pop(0)

            if getattr(self.context, "egging_enabled", False):
                self._spawn_egg(world, click_x, click_y)
            elif getattr(self.context, "feeding_enabled", False):
                self._spawn_pellet(world, click_x, click_y)
        # done