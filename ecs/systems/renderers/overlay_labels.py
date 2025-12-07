# ecs/systems/renderers/overlay_labels.py
import pygame
from ecs.components.fish.hunger_component import Hunger
from ecs.components.fish.health_component import Health
from ecs.components.fish.brain_component import Brain
from .cache import LabelCache
from ecs.components.fish.age_component import Age


def _state_color(state: str):
    return {
        "Cruise": (120, 200, 255),
        "Idle": (255, 220, 120),
        "Dead": (255, 120, 120),
        "LookForFood": (180, 255, 255),
        "ChaseFood": (255, 255, 180),
    }.get(state, (255, 255, 255))

def draw_state_and_bars(screen, label_cache: LabelCache,
                        draw_x: float, draw_y: float, screen_w: int, screen_h: int,
                        brain: Brain, hunger: Hunger, health: Health, age: Age,
                        *, show_labels: bool, bar_h: int, bar_gap: int, label_offset: int):
    if show_labels and brain:
        stage_suffix = ""
        if age:
            stage_suffix = f" [{age.stage}]"
        text = f"{brain.state}{stage_suffix}"
        surf = label_cache.get(text, _state_color(brain.state))
        screen.blit(surf, (draw_x, draw_y + screen_h + label_offset))
    if show_labels and hunger and health:
        hunger_ratio = hunger.hunger / max(1e-6, hunger.hunger_max)
        health_ratio = health.value / max(1e-6, health.max_value)
        bar_w = screen_w
        # Hunger bar
        bar_x = draw_x
        bar_y = draw_y - (bar_gap + bar_h)
        pygame.draw.rect(screen, (60, 60, 60), (bar_x, bar_y, bar_w, bar_h))
        pygame.draw.rect(screen, (255, 210, 80), (bar_x, bar_y, int(bar_w * hunger_ratio), bar_h))
        # Health bar
        bar_y -= bar_gap
        pygame.draw.rect(screen, (60, 60, 60), (bar_x, bar_y, bar_w, bar_h))
        pygame.draw.rect(screen, (100, 255, 120), (bar_x, bar_y, int(bar_w * health_ratio), bar_h))
    # Age bar (progress through lifespan) — shown with labels on
    if show_labels and age:
        age_ratio = max(0.0, min(1.0, age.age / max(1e-6, age.lifespan)))
        bar_w = screen_w
        bar_x = draw_x
        bar_y = draw_y - (bar_gap + bar_h) * 3  # stack below the others
        # background
        pygame.draw.rect(screen, (60, 60, 60), (bar_x, bar_y, bar_w, bar_h))
        # fill (cool→warm as it ages)
        # simple 2-color lerp from light blue to orange
        r = int(120 + (255 - 120) * age_ratio)
        g = int(200 + (140 - 200) * age_ratio)
        b = int(255 + ( 60 - 255) * age_ratio)
        pygame.draw.rect(screen, (r, g, b), (bar_x, bar_y, int(bar_w * age_ratio), bar_h))
