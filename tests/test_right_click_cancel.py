# tests/test_right_click_cancel.py
import os
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame
import pytest

from world import World
from game_context import GameContext
from ecs.systems.ui.mouse_system import MouseSystem
from ecs.systems.ui.fish_window_system import FishWindowSystem

RMB = 3

@pytest.fixture(scope="module", autouse=True)
def _pg():
    pygame.init()
    try:
        pygame.display.set_mode((800, 600))
        yield
    finally:
        pygame.quit()

def _make_ctx_assets_screen():
    ctx = GameContext()
    screen = pygame.display.get_surface()
    # toolbar rects so state exists
    ctx.toolbar_button_rect = pygame.Rect(10, 10, 60, 30)
    ctx.toolbar_egg_rect = pygame.Rect(80, 10, 60, 30)
    ctx.assets = type("A", (), {"get": lambda *_: pygame.Surface((1,1), pygame.SRCALPHA)})()
    return ctx, screen

def _mouse_system(ctx, screen):
    return MouseSystem(ctx, screen, ctx.assets)

def _open_modal(ctx, screen, world):
    ctx.show_fish_window = True
    FishWindowSystem(screen, ctx.assets, ctx).update(world, 0.016)
    pygame.display.flip()

def _rmb_up(ms: MouseSystem, x: int, y: int):
    evt = pygame.event.Event(pygame.MOUSEBUTTONUP, {"pos": (x, y), "button": RMB})
    ms.handle_mouse_event(evt)

def test_rmb_closes_modal_and_clears_tools_and_flags():
    world = World()
    ctx, screen = _make_ctx_assets_screen()

    # Enable both tools to verify they get cleared by RMB
    ctx.egging_enabled = True
    ctx.feeding_enabled = True

    # Open the modal (Fish window)
    _open_modal(ctx, screen, world)

    # Preconditions: strict modal flags and rects should be present
    assert getattr(ctx, "ui_modal_active", False) is True
    assert getattr(ctx, "fish_window_rect", None) is not None
    assert getattr(ctx, "fish_close_rect", None) is not None
    assert ctx.show_fish_window is True

    # Inject right-click (on mouse UP)
    ms = _mouse_system(ctx, screen)
    _rmb_up(ms, 10, 10)

    # Postconditions
    assert ctx.show_fish_window is False, "RMB-UP should close fish modal immediately"
    assert getattr(ctx, "egging_enabled", False) is False
    assert getattr(ctx, "feeding_enabled", False) is False

def test_rmb_without_modal_disables_tools_but_keeps_modal_flags_off():
    world = World()
    ctx, screen = _make_ctx_assets_screen()

    # Ensure modal is not open
    ctx.show_fish_window = False
    ctx.ui_modal_active = False
    ctx.ui_modal_whitelist = []

    # Turn tools on
    ctx.egging_enabled = True
    ctx.feeding_enabled = True

    # RMB-UP
    ms = _mouse_system(ctx, screen)
    _rmb_up(ms, 100, 100)

    # Tools should be off; modal flags remain off
    assert getattr(ctx, "egging_enabled", False) is False
    assert getattr(ctx, "feeding_enabled", False) is False
    assert getattr(ctx, "ui_modal_active", False) is False
