# ecs/systems/fish_overlay_system.py
import pygame
from typing import Optional
from ecs.components.core.position_component import Position
from ecs.components.core.sprite_component import Sprite
from ecs.components.core.tank_ref_component import TankRef
from ecs.components.core.velocity_component import Velocity
from ecs.components.fish.brain_component import Brain
from ecs.components.fish.hunger_component import Hunger
from ecs.components.fish.health_component import Health
from ecs.components.fish.behavior_tuning import BehaviorTuning
from ecs.components.fish.target_intent_component import TargetIntent
from ecs.components.fish.steering_intent_component import SteeringIntent
from ecs.components.fish.age_component import Age
from ecs.systems.renderers import (
    LabelCache,
    choose_facing,
    draw_state_and_bars,
    draw_food_debug,
    draw_target_line_from_mouth,
    draw_velocity_arrow,
    draw_avoidance_arrow,
)


class FishOverlaySystem:
    def __init__(self, screen, assets, context, font_size: int = 14):
        self.screen = screen
        self.assets = assets
        self.context = context

        # Font safety for headless/tests
        if not pygame.get_init():
            pygame.init()  # why: avoid crashes in ad-hoc/manual runs
        if not pygame.font.get_init():
            pygame.font.init()

        self.font = pygame.font.SysFont("arial", font_size)

        # Caches/state
        self.label_cache = LabelCache(self.font)  # cached text surfaces
        self._last_facing: dict[int, bool] = {}   # eid -> faces_right

        # UI sizing (stable defaults; tweak via context if present)
        self._bar_h = int(getattr(self.context, "overlay_bar_h", 8))
        self._bar_gap = int(getattr(self.context, "overlay_bar_gap", 4))
        # y-offset (in px) for state label relative to sprite top
        self._label_offset = int(getattr(self.context, "overlay_label_offset", -4))

    def update(self, world, dt):
        scale = float(getattr(self.context, "tank_scale", 1.0))

        for e in world.entities_with(Position, Sprite):
            pos: Position = world.get_component(e, Position)
            spr: Sprite = world.get_component(e, Sprite)
            vel: Optional[Velocity] = world.get_component(e, Velocity)
            brain: Optional[Brain] = world.get_component(e, Brain)
            hunger: Optional[Hunger] = world.get_component(e, Hunger)
            health: Optional[Health] = world.get_component(e, Health)
            tuning: Optional[BehaviorTuning] = world.get_component(e, BehaviorTuning)
            target: Optional[TargetIntent] = world.get_component(e, TargetIntent)
            steering: Optional[SteeringIntent] = world.get_component(e, SteeringIntent)
            tank_ref: Optional[TankRef] = world.get_component(e, TankRef)
            tank_pos: Optional[Position] = world.get_component(tank_ref.tank_entity, Position) if tank_ref else None
            age: Optional[Age] = world.get_component(e, Age)

            # Only fish linked to a tank get overlays
            if tank_pos is None:
                continue

            # Facing state (persistent for stable mouth anchoring)
            last_face = self._last_facing.get(e, bool(getattr(spr, "faces_right", True)))
            face_right, _ = choose_facing(spr, vel, target, pos, last_face)
            self._last_facing[e] = face_right

            # On-screen rect
            draw_x = int(round(tank_pos.x + pos.x * scale))
            draw_y = int(round(tank_pos.y + pos.y * scale))
            screen_w = int(round(spr.base_w * scale))
            screen_h = int(round(spr.base_h * scale))

            # 1) State label + hunger/health bars
            draw_state_and_bars(
                self.screen,
                self.label_cache,
                draw_x,
                draw_y,
                screen_w,
                screen_h,
                brain,
                hunger,
                health,
                age,
                show_labels=bool(getattr(self.context, "show_behavior_labels", True)),
                bar_h=self._bar_h,
                bar_gap=self._bar_gap,
                label_offset=self._label_offset,
            )

            # 2) Food overlays (vision ring, pellet radius, mouth circle + link)
            draw_food_debug(
                self.screen,
                world,
                self.context,
                pos,
                spr,
                brain,
                tuning,
                face_right,
                tank_pos,
                scale,
                draw_x,
                draw_y,
                screen_w,
                screen_h,
            )

            # 3) Target line from mouth
            draw_target_line_from_mouth(
                self.screen,
                self.context,
                pos,
                spr,
                brain,
                face_right,
                tank_pos,
                scale,
                draw_x,
                draw_y,
                screen_w,
                screen_h,
            )

            # 4) Motion vectors
            draw_velocity_arrow(self.screen, self.context, draw_x, draw_y, screen_w, screen_h, vel)
            draw_avoidance_arrow(self.screen, self.context, draw_x, draw_y, screen_w, screen_h, steering)
