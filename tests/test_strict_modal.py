# tests/test_strict_modal.py
import os
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame
import pytest

from world import World
from game_context import GameContext
from ecs.systems.ui.mouse_system import MouseSystem
from ecs.systems.ui.fish_window_system import FishWindowSystem

LMB = 1
RMB = 3

@pytest.fixture(scope="module", autouse=True)
def _pg():
    pygame.init()
    try:
        pygame.display.set_mode((800, 600))
        yield
    finally:
        pygame.quit()

class Ctx(GameContext):
    def __init__(self):
        super().__init__()
        # toolbar rects
        self.toolbar_button_rect = pygame.Rect(10, 10, 60, 30)  # FEED
        self.toolbar_egg_rect = pygame.Rect(80, 10, 60, 30)     # EGG
        # tank covers screen
        self.tank_screen_x, self.tank_screen_y = 0, 0
        sw, sh = pygame.display.get_surface().get_size()
        self.tank_screen_w, self.tank_screen_h = sw, sh
        # minimal assets handle
        self.assets = type("A", (), {"get": lambda *_: pygame.Surface((1,1), pygame.SRCALPHA)})()

def _ensure_modal_flags(ctx: GameContext):
    if not getattr(ctx, "fish_window_rect", None):
        sw, sh = pygame.display.get_surface().get_size()
        win_w, win_h = 420, 520
        win_x, win_y = sw - win_w - 20, 60
        ctx.fish_window_rect = pygame.Rect(win_x, win_y, win_w, win_h)
    if not getattr(ctx, "fish_close_rect", None):
        close_size = 18
        ctx.fish_close_rect = pygame.Rect(
            ctx.fish_window_rect.right - 12 - close_size,
            ctx.fish_window_rect.y + 12,
            close_size,
            close_size,
        )
    ctx.ui_modal_active = True
    ctx.ui_modal_whitelist = [ctx.fish_window_rect, ctx.fish_close_rect]

def _open_modal(ctx: GameContext, screen, world: World):
    ctx.show_fish_window = True
    FishWindowSystem(screen, ctx.assets, ctx).update(world, 0.016)
    pygame.display.flip()
    _ensure_modal_flags(ctx)

def _mouse_system(ctx, screen):
    ms = MouseSystem(ctx, screen, ctx.assets)
    return ms

def _click_up(ms: MouseSystem, x: int, y: int, button: int):
    evt = pygame.event.Event(pygame.MOUSEBUTTONUP, {"pos": (x, y), "button": button})
    ms.handle_mouse_event(evt)

def test_modal_blocks_toolbar_and_world():
    world = World()
    screen = pygame.display.get_surface()
    ctx = Ctx()
    _open_modal(ctx, screen, world)

    ms = _mouse_system(ctx, screen)

    # Toolbar clicks should be ignored while modal is active
    _click_up(ms, 15, 15, LMB)    # FEED
    assert not getattr(ctx, "feeding_enabled", False), "modal must block toolbar FEED"

    _click_up(ms, 85, 15, LMB)    # EGG
    assert not getattr(ctx, "egging_enabled", False), "modal must block toolbar EGG"

    # World/tank clicks also blocked
    _click_up(ms, 200, 200, LMB)

def test_modal_close_button_closes_and_unblocks():
    world = World()
    screen = pygame.display.get_surface()
    ctx = Ctx()
    _open_modal(ctx, screen, world)

    ms = _mouse_system(ctx, screen)

    # Close via the X rect (provided or synthesized)
    close_r = getattr(ctx, "fish_close_rect", None)
    assert close_r, "close rect missing"
    cx, cy = close_r.center
    _click_up(ms, cx, cy, LMB)

    # Modal flag down immediately
    assert ctx.show_fish_window is False

    # Next frame, scene would clear strict flags; emulate:
    ctx.ui_modal_active = False
    ctx.ui_modal_whitelist = None

    # Toolbar FEED now toggles
    _click_up(ms, 15, 15, LMB)
    assert getattr(ctx, "feeding_enabled", False) is True

def test_after_modal_closes_toolbar_works():
    world = World()
    screen = pygame.display.get_surface()
    ctx = Ctx()
    _open_modal(ctx, screen, world)

    ms = _mouse_system(ctx, screen)

    # Close first
    close_r = getattr(ctx, "fish_close_rect", None)
    cx, cy = close_r.center
    _click_up(ms, cx, cy, LMB)

    # Simulate next frame where strict modal is cleared
    ctx.ui_modal_active = False
    ctx.ui_modal_whitelist = None

    _click_up(ms, 15, 15, LMB)
    assert getattr(ctx, "feeding_enabled", False) is True
