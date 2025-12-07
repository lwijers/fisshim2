# tests/test_panel_manager_grid.py
import os
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame
import pytest

from types import SimpleNamespace

# Systems under test
from ecs.systems.ui.widgets.panel_manager_system import PanelManagerSystem
from ecs.systems.ui.mouse_system import MouseSystem

# --- Minimal world/components stubs ---

class _Species:
    def __init__(self, display_name: str, species_id: str = "goldfish"):
        self.display_name = display_name
        self.species_id = species_id

class _WorldStub:
    """Enough of the world API for PanelManagerSystem.open_fish(...) title lookup."""
    def get_component(self, entity_id, comp_type):
        if comp_type.__name__ == "Species":
            return _Species(display_name=f"Fish {entity_id}")
        return None

# --- Pygame bootstrap ---

@pytest.fixture(scope="module", autouse=True)
def _pygame_boot():
    pygame.init()
    try:
        # a modest screen; PanelManagerSystem reads size for grid math
        pygame.display.set_mode((800, 600))
        yield
    finally:
        pygame.quit()


def _make_ctx_screen_assets():
    ctx = SimpleNamespace()
    ctx.ui = {}             # optional UI config dict
    ctx.ui_panels = []      # PanelManager populates/reads this
    # legacy flags used by MouseSystem global cancel path (kept harmless)
    ctx.show_fish_window = False
    ctx.show_fish_inspector = False

    screen = pygame.display.get_surface()
    assets = SimpleNamespace()  # not used by these tests
    return ctx, screen, assets


# -----------------------------
# Tests
# -----------------------------

def test_open_panels_are_compact_grid_from_top_left():
    """
    Open three panels and verify they occupy slot 0,1,2 (top-left grid, left->right then wrap).
    """
    ctx, screen, assets = _make_ctx_screen_assets()
    mgr = PanelManagerSystem(screen, assets, ctx)
    world = _WorldStub()

    # Open three distinct fish panels
    mgr.open_fish(world, 101)
    mgr.open_fish(world, 202)
    mgr.open_fish(world, 303)

    assert len(ctx.ui_panels) == 3

    # Expected positions according to manager's own grid function
    exp0 = mgr._grid_slot_xy(0)
    exp1 = mgr._grid_slot_xy(1)
    exp2 = mgr._grid_slot_xy(2)

    # Actual positions
    p0, p1, p2 = ctx.ui_panels[0], ctx.ui_panels[1], ctx.ui_panels[2]
    got0 = (p0.x, p0.y)
    got1 = (p1.x, p1.y)
    got2 = (p2.x, p2.y)

    assert got0 == exp0, f"slot 0 mismatch: got {got0}, expected {exp0}"
    assert got1 == exp1, f"slot 1 mismatch: got {got1}, expected {exp1}"
    assert got2 == exp2, f"slot 2 mismatch: got {got2}, expected {exp2}"


def test_rmb_closes_top_panel_lifo_and_reflows_compact(monkeypatch):
    """
    RMB-up closes the top-most panel (highest z). After each close, remaining panels reflow
    to compact grid slots (0..n-1).
    """
    ctx, screen, assets = _make_ctx_screen_assets()
    mgr = PanelManagerSystem(screen, assets, ctx)
    world = _WorldStub()

    # Wire MouseSystem to route RMB closings into panel manager
    mouse = MouseSystem(ctx, screen, assets)
    mouse.set_panel_manager(mgr)
    mouse.set_world_ref(world)  # not used in this test, safe

    # Build three panels; last opened should be the top-most (highest z)
    mgr.open_fish(world, 1)
    mgr.open_fish(world, 2)
    mgr.open_fish(world, 3)

    assert len(ctx.ui_panels) == 3

    # Simulate RMB-up (MouseSystem uses pygame.mouse.get_pos())
    monkeypatch.setattr(pygame.mouse, "get_pos", lambda: (0, 0))
    evt_rmb = pygame.event.Event(pygame.MOUSEBUTTONUP, {"button": 3, "pos": (0, 0)})

    # First RMB should close the top-most (fish 3)
    mouse.handle_mouse_event(evt_rmb)
    assert len(ctx.ui_panels) == 2, "expected one panel to be closed by first RMB"
    # Remaining panels must occupy slots 0 and 1 compactly
    exp0 = mgr._grid_slot_xy(0)
    exp1 = mgr._grid_slot_xy(1)
    got_pos = {(p.x, p.y) for p in ctx.ui_panels}
    assert exp0 in got_pos and exp1 in got_pos, f"panels not reflowed compactly after close; got {got_pos}, expected {exp0} & {exp1}"

    # Second RMB should close the next top-most → 1 panel remains at slot 0
    mouse.handle_mouse_event(evt_rmb)
    assert len(ctx.ui_panels) == 1, "expected two panels closed after second RMB"
    exp0 = mgr._grid_slot_xy(0)
    only = ctx.ui_panels[0]
    assert (only.x, only.y) == exp0, f"remaining panel not at slot 0 after reflow; got {(only.x, only.y)}, expected {exp0}"

    # Third RMB should close the last panel; then it falls back to global cancel (no crash)
    mouse.handle_mouse_event(evt_rmb)
    assert len(ctx.ui_panels) == 0, "expected all panels closed after third RMB"
