# tests/test_fish_window_thumbs.py
import os
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame
import pytest

from world import World
from game_context import GameContext
from ecs.components.core.position_component import Position
from ecs.components.core.bounds_component import Bounds
from ecs.components.core.tank_component import Tank
from ecs.components.core.tank_ref_component import TankRef
from ecs.components.core.sprite_component import Sprite
from ecs.components.fish.age_component import Age
from ecs.components.fish.brain_component import Brain
from ecs.components.fish.species_component import Species
from ecs.components.fish.hunger_component import Hunger
from ecs.components.fish.health_component import Health
from ecs.systems.rendering.sprite_render_system import SpriteRenderSystem
from ecs.systems.ui.fish_window_system import FishWindowSystem
from ecs.systems.renderers.cache import SpriteCache

# ---------------------------------------------------------------------------
# Pygame bootstrap
# ---------------------------------------------------------------------------
@pytest.fixture(scope="module", autouse=True)
def _pygame_boot():
    pygame.init()
    try:
        pygame.display.set_mode((1, 1))
        yield
    finally:
        pygame.quit()

# ---------------------------------------------------------------------------
# Minimal assets - deterministic base sprites
# ---------------------------------------------------------------------------
class _Assets:
    def __init__(self):
        self.images = {}
        self.images["goldfish"] = pygame.Surface((60, 40), pygame.SRCALPHA)
        # distinct vivid color
        self.images["goldfish"].fill((100, 160, 255, 255))

    def get(self, key):
        return self.images.get(key)

# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------
def _tank(world):
    t = world.create_entity()
    world.add_component(t, Tank())
    world.add_component(t, Position(50.0, 50.0))
    world.add_component(t, Bounds(400, 300))
    return t

def _fish(world, tank, stage="Adult", brain="Cruise"):
    e = world.create_entity()
    world.add_component(e, TankRef(tank))
    world.add_component(e, Position(120.0, 120.0))
    world.add_component(e, Sprite("goldfish", 60, 40))
    world.add_component(e, Age(age=0.0, lifespan=100.0, stage=stage, pre_hatch=0.0))
    world.add_component(e, Brain(state=brain))
    # IMPORTANT: include these so FishWindow lists the fish as a card
    world.add_component(e, Species(species_id="goldfish", display_name="Goldfish", base_speed=150.0))
    world.add_component(e, Hunger(hunger=50.0, hunger_rate=1.0, hunger_max=100.0))
    world.add_component(e, Health(value=100.0, max_value=100.0))
    return e

def _make_ctx_assets_screen():
    ctx = GameContext()
    ctx.assets = _Assets()
    screen = pygame.display.set_mode((800, 600))
    return ctx, screen

# ---------------------------------------------------------------------------
# Helpers to render and inspect the scaling used for the thumbnail
# ---------------------------------------------------------------------------
def _draw_fish_window(ctx, screen, world):
    ctx.show_fish_window = True
    win = FishWindowSystem(screen, ctx.assets, ctx)
    win.update(world, dt=0.016)
    pygame.display.flip()
    return win

class _ScaleCapture:
    """
    Wrap pygame.transform.smoothscale to capture (w,h) and detect if the
    *source* surface appears grayscale (r≈g≈b at a sample).
    """
    def __init__(self):
        self.calls = []  # list of dicts with 'size':(w,h), 'src_grey':bool

    def _looks_grey(self, surf: pygame.Surface) -> bool:
        # sample a few pixels; treat equal RGB as grayscale
        w, h = surf.get_size()
        pts = [(w//2, h//2), (1, 1), (w-2 if w>2 else 0, h-2 if h>2 else 0)]
        for x, y in pts:
            r, g, b, a = surf.get_at((x, y))
            if a > 0 and (r != g or g != b):
                return False
        return True

    def wrap(self, orig):
        def _wrapped(src, size):
            w, h = size
            src_grey = self._looks_grey(src)
            self.calls.append({"size": (int(w), int(h)), "src_grey": src_grey})
            # return a plain surface of the requested size (content not used)
            out = pygame.Surface((int(w), int(h)), pygame.SRCALPHA)
            out.fill((200, 200, 200, 255) if src_grey else (10, 200, 10, 255))
            return out
        return _wrapped

def _wrap_spritecache_get_for_capture():
    """Return (calls, wrapper) where calls.first captures the first get() usage."""
    class _Calls:
        def __init__(self):
            self.first = None
            self.all = []

        def record_first(self, **kwargs):
            if self.first is None:
                self.first = kwargs.copy()
            self.all.append(kwargs.copy())

    calls = _Calls()
    original_get = SpriteCache.shared().get

    def wrapped_get(img, w, h, *, dead=False, hflip=False, variant="normal", senior_style=None):
        calls.record_first(
            w=int(w), h=int(h),
            dead=bool(dead), hflip=bool(hflip),
            variant=variant,
            senior_style=senior_style,
            src_size=(img.get_width(), img.get_height()) if isinstance(img, pygame.Surface) else None,
        )
        return original_get(img, w, h, dead=dead, hflip=hflip, variant=variant, senior_style=senior_style)

    return calls, wrapped_get

# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
def test_card_adult_is_full_size_and_centered(monkeypatch):
    world = World()
    ctx, screen = _make_ctx_assets_screen()
    tank = _tank(world)
    _fish(world, tank, stage="Adult", brain="Cruise")

    cap = _ScaleCapture()
    monkeypatch.setattr(pygame.transform, "smoothscale", cap.wrap(pygame.transform.smoothscale))

    _draw_fish_window(ctx, screen, world)

    # Expect a scale call for the card thumbnail
    assert cap.calls, "no scaling calls captured for adult thumbnail"
    # Use the first scale call—thumbnail creation
    (w, h) = cap.calls[0]["size"]
    # Base: 60x40 into 72x72 box ⇒ 72x48
    assert (w, h) == (72, 48), f"adult thumb size wrong: got {(w,h)} expected (72,48)"
    # Not grayscale
    assert cap.calls[0]["src_grey"] is False, "adult should not be grayscale"

def test_card_juvenile_is_half_size_and_centered(monkeypatch):
    world = World()
    ctx, screen = _make_ctx_assets_screen()
    tank = _tank(world)
    _fish(world, tank, stage="Juvenile", brain="Cruise")

    cap = _ScaleCapture()
    monkeypatch.setattr(pygame.transform, "smoothscale", cap.wrap(pygame.transform.smoothscale))

    _draw_fish_window(ctx, screen, world)

    assert cap.calls, "no scaling calls captured for juvenile thumbnail"
    (w, h) = cap.calls[0]["size"]
    # Juvenile box: 36x36 ⇒ base 60x40 → 36x24
    assert (w, h) == (36, 24), f"juvenile thumb size wrong: got {(w,h)} expected (36,24)"
    assert cap.calls[0]["src_grey"] is False

def test_card_dead_uses_dead_variant_and_size(monkeypatch):
    world = World()
    ctx, screen = _make_ctx_assets_screen()
    tank = _tank(world)
    _fish(world, tank, stage="Adult", brain="Dead")

    # Publish finals (okay either way; card thumbs use base+variant, but harmless)
    SpriteRenderSystem(screen, ctx.assets, ctx).update(world, dt=0.016)

    # Capture the exact arguments FishWindow uses for the thumbnail build
    captured = {}
    original_get = SpriteCache.shared().get

    def wrapped_get(img, w, h, *, dead=False, hflip=False, variant="normal", senior_style=None):
        # record first call only (first card)
        if not captured:
            captured.update(dict(w=int(w), h=int(h), dead=bool(dead), hflip=bool(hflip), variant=variant))
        return original_get(img, w, h, dead=dead, hflip=hflip, variant=variant, senior_style=senior_style)

    monkeypatch.setattr(SpriteCache.shared(), "get", wrapped_get)

    # Also keep scaling capture to ensure the size path runs
    cap = _ScaleCapture()
    monkeypatch.setattr(pygame.transform, "smoothscale", cap.wrap(pygame.transform.smoothscale))

    _draw_fish_window(ctx, screen, world)

    # Ensure we actually built a thumb
    assert captured, "no SpriteCache.get call captured for dead thumbnail"

    # Dead adult uses adult geometry (base 60x40 inside 72x72 box) -> 72x48
    assert (captured["w"], captured["h"]) == (72, 48), f"dead size wrong: got {(captured['w'], captured['h'])}, expected (72, 48)"
    assert captured["dead"] is True, "dead thumbnail must request dead=True (grayscale+vflip path)"
    assert captured["hflip"] is False, "card thumbs must keep stable facing (no live hflip)"
    # Variant can be "normal" for adult, since 'dead' flag drives the grayscale/vflip.

def test_card_egg_uses_egg_asset_and_fits_box(monkeypatch):
    """
    Egg thumbnails must use the 'egg' asset, fitted to the card box (72x72).
    """
    world = World()
    ctx, screen = _make_ctx_assets_screen()
    tank = _tank(world)
    _fish(world, tank, stage="Egg", brain="Cruise")

    # Publish finals (harmless for cards, keeps parity with other tests)
    SpriteRenderSystem(screen, ctx.assets, ctx).update(world, dt=0.016)

    # Provide a known egg surface and capture asset key usage
    egg_surface = pygame.Surface((40, 40), pygame.SRCALPHA)
    seen_keys = []
    original_assets_get = ctx.assets.get

    def assets_get(key):
        seen_keys.append(key)
        if key == "egg":
            return egg_surface
        return original_assets_get(key)

    monkeypatch.setattr(ctx.assets, "get", assets_get)

    # Capture SpriteCache.get usage
    calls, wrapped = _wrap_spritecache_get_for_capture()
    monkeypatch.setattr(SpriteCache.shared(), "get", wrapped)

    _draw_fish_window(ctx, screen, world)

    assert calls.first is not None, "no SpriteCache.get call captured for egg thumbnail"
    assert "egg" in seen_keys, f"egg asset not requested; seen keys: {seen_keys}"
    # Square egg 40x40 into 72 box => 72x72
    assert (calls.first["w"], calls.first["h"]) == (72, 72), f"egg size wrong: got {(calls.first['w'], calls.first['h'])}"
    assert calls.first["dead"] is False
    assert calls.first["variant"] == "normal"

def test_card_senior_uses_senior_variant_and_size(monkeypatch):
    """
    Senior (alive) thumbnails must use variant='senior' with style and adult geometry (72x48).
    """
    world = World()
    ctx, screen = _make_ctx_assets_screen()
    tank = _tank(world)
    _fish(world, tank, stage="Senior", brain="Cruise")

    SpriteRenderSystem(screen, ctx.assets, ctx).update(world, dt=0.016)

    calls, wrapped = _wrap_spritecache_get_for_capture()
    monkeypatch.setattr(SpriteCache.shared(), "get", wrapped)

    _draw_fish_window(ctx, screen, world)

    assert calls.first is not None, "no SpriteCache.get call captured for senior thumbnail"
    assert (calls.first["w"], calls.first["h"]) == (72, 48), f"senior size wrong: got {(calls.first['w'], calls.first['h'])}, expected (72,48)"
    assert calls.first["dead"] is False
    assert calls.first["variant"] == "senior", f"expected variant=senior, got {calls.first['variant']}"
    style = calls.first["senior_style"]
    assert isinstance(style, dict) and "desaturate" in style and "tint" in style, f"missing senior style fields: {style}"

def test_card_senior_dead_uses_dead_variant_not_senior(monkeypatch):
    """
    Senior+Dead must request dead=True and NOT apply senior variant; size stays adult geometry (72x48).
    """
    world = World()
    ctx, screen = _make_ctx_assets_screen()
    tank = _tank(world)
    _fish(world, tank, stage="Senior", brain="Dead")

    SpriteRenderSystem(screen, ctx.assets, ctx).update(world, dt=0.016)

    calls, wrapped = _wrap_spritecache_get_for_capture()
    monkeypatch.setattr(SpriteCache.shared(), "get", wrapped)

    _draw_fish_window(ctx, screen, world)

    assert calls.first is not None, "no SpriteCache.get call captured for senior-dead thumbnail"
    assert (calls.first["w"], calls.first["h"]) == (72, 48)
    assert calls.first["dead"] is True
    assert calls.first["variant"] == "normal", f"dead senior should not use 'senior' variant, got {calls.first['variant']}"
