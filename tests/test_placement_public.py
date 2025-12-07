# tests/test_placement_public.py
import math
import pytest

from ecs.systems.ui.placement_system import PlacementSystem

from ecs.components.core.position_component import Position
from ecs.components.core.sprite_component import Sprite
from ecs.components.core.tank_ref_component import TankRef
from ecs.components.tags.food_pellet_component import FoodPellet

from tests.helpers import make_world, make_context


# --- World compatibility helpers --------------------------------------------

def _get_component(world, e, Comp):
    """
    Return component instance or None, working across different ECS 'World' APIs.
    Tries: get_component -> component_for_entity -> components_for_entity
    """
    # Most common in your project
    if hasattr(world, "get_component"):
        try:
            return world.get_component(e, Comp)
        except Exception:
            pass

    # Esper-like
    if hasattr(world, "component_for_entity"):
        try:
            return world.component_for_entity(e, Comp)
        except Exception:
            return None

    # Fallback: scan tuple from components_for_entity if available
    if hasattr(world, "components_for_entity"):
        try:
            comps = world.components_for_entity(e)
            for c in comps:
                if isinstance(c, Comp):
                    return c
        except Exception:
            pass

    return None


def _has_component(world, e, Comp) -> bool:
    # If the world *does* provide has_component, use it.
    hc = getattr(world, "has_component", None)
    if callable(hc):
        try:
            return bool(hc(e, Comp))
        except Exception:
            # fall through to generic check
            pass
    return _get_component(world, e, Comp) is not None


def _iter_entities(world):
    """
    Robustly iterate entities whether world.entities is a method or a collection.
    """
    ents_attr = getattr(world, "entities", None)
    if callable(ents_attr):
        try:
            return list(ents_attr())
        except TypeError:
            pass
    elif ents_attr is not None:
        try:
            return list(ents_attr)
        except TypeError:
            pass

    # Other common names
    for name in ("all_entities", "_entities"):
        cand = getattr(world, name, None)
        if cand is None:
            continue
        if callable(cand):
            try:
                return list(cand())
            except TypeError:
                continue
        try:
            return list(cand)
        except TypeError:
            continue

    return []


# --- Click wiring helper -----------------------------------------------------

def _send_click(sys, world, x, y):
    """
    Try common public APIs. Return True if we managed to send a click.
    Prefers PlacementSystem.enqueue_click which your system exposes.
    """
    for name in ("enqueue_click", "on_click", "queue_click", "handle_click", "emit_click"):
        fn = getattr(sys, name, None)
        if callable(fn):
            fn(x, y)
            return True

    # Public queue attribute
    if hasattr(sys, "clicks") and isinstance(sys.clicks, list):
        sys.clicks.append((x, y))
        return True

    # Event-based fallback (optional)
    event_classes = []
    for dotted in (
        "ecs.components.input.click_event.ClickEvent",
        "ecs.components.input.mouse_click.MouseClick",
        "ecs.components.input.events.MouseClick",
    ):
        try:
            module_path, cls_name = dotted.rsplit(".", 1)
            mod = __import__(module_path, fromlist=[cls_name])
            event_classes.append(getattr(mod, cls_name))
        except Exception:
            pass

    if event_classes:
        Evt = event_classes[0]
        e = world.create_entity()
        world.add_component(e, Evt(x=int(x), y=int(y)))
        return True

    return False


def _find_spawned_pellets(world):
    pellets = []
    for e in _iter_entities(world):
        if _has_component(world, e, FoodPellet) and _has_component(world, e, Position):
            pellets.append((e, _get_component(world, e, Position)))
    return pellets


# --- The test ----------------------------------------------------------------

def test_click_spawns_pellet_at_logical_click_point():
    """
    PlacementSystem:
      - expects enqueue_click(x, y)
      - spawns pellets when context.feeding_enabled is True
      - requires set_tank(tank_entity) and that tank has a Position
      - maps screen (x, y) -> logical ((x - sx)/scale, (y - sy)/scale)
    """
    world = make_world()
    ctx = make_context()

    # Screen rect and scale for screen->logical mapping
    ctx.tank_screen_x = 100
    ctx.tank_screen_y = 100
    ctx.tank_screen_w = 600
    ctx.tank_screen_h = 400
    ctx.tank_scale = 1.0
    ctx.feeding_enabled = True

    # Create a tank entity and register it with the system
    tank = world.create_entity()
    world.add_component(tank, Position(0.0, 0.0))
    world.add_component(tank, TankRef(tank))
    world.add_component(tank, Sprite("tank", base_w=600, base_h=400))

    sys = PlacementSystem(ctx)
    sys.set_tank(tank)

    # Click at screen center horizontally, 1/4 down vertically
    click_x = ctx.tank_screen_x + ctx.tank_screen_w // 2   # 100 + 300 = 400
    click_y = ctx.tank_screen_y + ctx.tank_screen_h // 4   # 100 + 100 = 200

    if not _send_click(sys, world, click_x, click_y):
        pytest.skip("PlacementSystem exposes no recognized click API/mode in this project")

    # Process the click this frame
    sys.update(world, dt=0.016)

    # Find spawned pellets
    pellets = _find_spawned_pellets(world)
    assert pellets, "No FoodPellet entity was spawned after click"

    # Assert expected logical position mapping
    _, pos = pellets[0]
    expected_x = (click_x - ctx.tank_screen_x) / ctx.tank_scale  # 300
    expected_y = (click_y - ctx.tank_screen_y) / ctx.tank_scale  # 100
    assert math.isclose(pos.x, expected_x, rel_tol=0.0, abs_tol=1e-6)
    assert math.isclose(pos.y, expected_y, rel_tol=0.0, abs_tol=1e-6)
