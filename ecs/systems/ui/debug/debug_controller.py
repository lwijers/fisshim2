# ecs/systems/ui/debug/debug_controller.py
from __future__ import annotations

# Public API ---------------------------------------------------------------

def ensure_defaults(ctx) -> None:
    """Idempotent defaults for menus + overlay flags."""
    _def(ctx, "show_debug_menu", False)     # F1
    _def(ctx, "show_motion_menu", False)    # F2
    _def(ctx, "show_food_menu", False)      # F3
    _def(ctx, "show_behavior_menu", False)  # F4
    _def(ctx, "show_swim_menu", False)      # F5

    # Movement
    _def(ctx, "show_target_lines", False)
    _def(ctx, "show_velocity_arrows", False)
    _def(ctx, "show_avoidance_arrows", False)

    # Food
    _def(ctx, "show_food_debug", False)  # umbrella if some renderers use it
    _def(ctx, "show_fish_vision", False)
    _def(ctx, "show_pellet_radius", False)
    _def(ctx, "show_food_links", False)

    # Behavior
    _def(ctx, "show_behavior_labels", False)
    _def(ctx, "show_stats_bars", False)

    # Swim
    _def(ctx, "show_swim_floor_debug", False)

def select_tab(ctx, tab: str) -> None:
    """
    Mutually-exclusive selection with toggle behavior.
    Allowed tabs: "legend","motion","food","behavior","swim".

    Behavior:
      - Pressing a new tab clears all overlays + opens that tab's menu + turns on its overlays.
      - Pressing the same tab again closes its menu and clears overlays (including target in food).
      - Food keeps target lines ON while active (exception only when turning food ON).
    """
    ensure_defaults(ctx)

    # Toggle off if this tab is already open
    if _is_tab_open(ctx, tab):
        _clear_all_menus(ctx)
        _clear_all_overlays(ctx)  # closes menu => overlays off
        return

    # Open requested tab: clear, then enable this tab
    _clear_all_menus(ctx)
    _clear_all_overlays(ctx)

    if tab == "legend":
        ctx.show_debug_menu = True
        return

    if tab == "motion":
        ctx.show_motion_menu = True
        ctx.show_target_lines = True
        ctx.show_velocity_arrows = True
        ctx.show_avoidance_arrows = True
        return

    if tab == "food":
        ctx.show_food_menu = True
        ctx.show_food_debug = True
        ctx.show_fish_vision = True
        ctx.show_pellet_radius = True
        ctx.show_food_links = True
        ctx.show_target_lines = True  # exception: keep target ON during food
        return

    if tab == "behavior":
        ctx.show_behavior_menu = True
        ctx.show_behavior_labels = True
        ctx.show_stats_bars = True
        return

    if tab == "swim":
        ctx.show_swim_menu = True
        ctx.show_swim_floor_debug = True
        return

# Internals ---------------------------------------------------------------

def _def(ctx, name, value):
    if not hasattr(ctx, name):
        setattr(ctx, name, value)

def _clear_all_menus(ctx):
    ctx.show_debug_menu = False
    ctx.show_motion_menu = False
    ctx.show_food_menu = False
    ctx.show_behavior_menu = False
    ctx.show_swim_menu = False

def _clear_all_overlays(ctx):
    # Movement
    ctx.show_target_lines = False
    ctx.show_velocity_arrows = False
    ctx.show_avoidance_arrows = False
    # Food
    ctx.show_food_debug = False
    ctx.show_fish_vision = False
    ctx.show_pellet_radius = False
    ctx.show_food_links = False
    # Behavior
    ctx.show_behavior_labels = False
    ctx.show_stats_bars = False
    # Swim
    ctx.show_swim_floor_debug = False

def _is_tab_open(ctx, tab: str) -> bool:
    if tab == "legend":   return bool(getattr(ctx, "show_debug_menu", False))
    if tab == "motion":   return bool(getattr(ctx, "show_motion_menu", False))
    if tab == "food":     return bool(getattr(ctx, "show_food_menu", False))
    if tab == "behavior": return bool(getattr(ctx, "show_behavior_menu", False))
    if tab == "swim":     return bool(getattr(ctx, "show_swim_menu", False))
    return False
