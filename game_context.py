# =========================
# file: game_context.py
# =========================
import const
from render.asset_manager import AssetManager
from utils.jsonio import load_json
import os

_BALANCING_DEFAULTS = {
    "movement_damping": 0.995,
    "wall_bounce": 0.30,
    "typical_max_speed": 40.0,
    "avoidance_margin": 20.0,
    "avoidance_max_strength": 0.25,
    "dead_sink_speed": 30.0,
    "state_speed_smoothing": 0.10,
    "idle_arrival_threshold": 6.0,
    "idle_bob_x_factor": 1.0,
    "idle_bob_y_factor": 0.8
}
_PELLET_DEFAULTS = {
    "sprite": "pellet",
    "width": 16,
    "height": 16,
    "radius_scale": 1.35,
    "nutrition": 40.0,
    "fall_speed": 60.0
}
_UI_DEFAULTS = {
    "render_cache_limit": 256,
    "ui_font_size": 14,
    "ui_bar_height": 4,
    "ui_bar_gap": 6,
    "ui_label_offset": 2,
    "ui_target_line_width": 1,
    "ui_velocity_arrow_scale": 0.5,
    "ui_avoidance_arrow_scale": 40.0,
    "ui_debug_border_width": 1,
}

# near other _DEFAULTS:
_AGING_DEFAULTS = {
    "elder_threshold_ratio": 0.80,
    "juvenile_threshold_ratio": 0.15,
    "elder_speed_multiplier_min": 0.70,
    "juvenile_speed_multiplier_min": 0.85,
    "elder_health_decay_at_max_per_sec": 0.04,
    "hard_death_at_lifespan": True,
    "egg_duration_sec": 12.0,
}


class GameContext:
    def __init__(self):
        self.running = True

        # Time scaling + pause
        self.time_scale = 1.0
        self._prev_time_scale = 1.0
        self.paused = False

        # Tank defaults (load file; fallback to prior hardcoded values)
        tank_defaults = load_json(os.path.join("data", "tank_defaults.json"), default={
            "logical_tank_width": 1000,
            "logical_tank_height": 600,
            "sand_top_ratio": 1.0
        })
        self.logical_tank_w = int(tank_defaults.get("logical_tank_width", 1000))
        self.logical_tank_h = int(tank_defaults.get("logical_tank_height", 600))
        # Used by pellet resting height, etc.
        self.sand_top_ratio = float(tank_defaults.get("sand_top_ratio", 1.0))

        # Resize state
        self.needs_resize = False
        self.new_screen_w = 0
        self.new_screen_h = 0

        # Computed tank transform
        self.tank_scale = 1.0
        self.tank_screen_x = 0
        self.tank_screen_y = 0
        self.tank_screen_w = self.logical_tank_w
        self.tank_screen_h = self.logical_tank_h
        self.swim_bottom_margin = int(tank_defaults.get("swim_bottom_margin", 64))

        # Debug flags (mirror const)
        self.show_behavior_labels   = const.DEBUG_SHOW_BEHAVIOR_LABELS
        self.show_stats_bars        = const.DEBUG_SHOW_STATS_BARS
        self.show_target_lines      = const.DEBUG_SHOW_TARGET_LINES
        self.show_velocity_arrows   = const.DEBUG_SHOW_VELOCITY_ARROWS
        self.show_avoidance_arrows  = const.DEBUG_SHOW_AVOIDANCE_ARROWS
        self.debug_sprite_border    = const.DEBUG_SHOW_SPRITE_BORDER
        self.debug_escape_quit      = const.DEBUG_ESCAPE_QUIT
        self.show_fish_vision       = const.DEBUG_SHOW_FISH_VISION
        self.show_pellet_radius     = const.DEBUG_SHOW_PELLET_RADIUS
        self.show_food_links        = const.DEBUG_SHOW_FOOD_LINKS
        self.show_debug_overlay     = False
        self.fps = 0.0

        # Data/config
        self.fish_defaults  = load_json(os.path.join("data", "fish_defaults.json"))
        self.species_config = load_json(os.path.join("data", "species.json"), default={})
        self.balancing      = load_json(os.path.join("data", "balancing.json"), default=_BALANCING_DEFAULTS)
        self.ui             = load_json(os.path.join("data", "ui_config.json"), default=_UI_DEFAULTS)
        self.pellets        = load_json(os.path.join("data", "pellets.json"), default=_PELLET_DEFAULTS)
        self.aging = load_json(os.path.join("data", "aging.json"), default=_AGING_DEFAULTS)
        self.breeding = load_json("data/breeding.json", default={
            "enabled": True,
            "mate_radius": 120.0,
            "pair_distance": 40.0,
            "courtship_time_sec": 6.0,
            "courtship_grace_sec": 0.3,
            "cooldown_sec": 30.0,
            "offspring_count_range": [1, 3],
            "min_health_ratio": 0.6,
            "min_hunger_ratio": 0.4,
            "max_population": 60
        })
        self.population_ok = True           # set by PopulationGuard
        self.test_seed = None
        # Assets
        self.assets = AssetManager()

        # --- UI/toolbar state ---
        self.feeding_enabled = False
        self.egging_enabled = False  # NEW: egg placement mode
        self.toolbar_button_rect = None  # feed button rect
        self.toolbar_egg_rect = None  # NEW: egg button rect

        # Optionally ensure UI defaults exist (used for egg sprite size)
        ui = self.ui or {}
        ui.setdefault("ui_egg_button_size", ui.get("ui_toolbar_button_size", 48))
        ui.setdefault("ui_egg_sprite_size", 28)  # fixed on-screen egg size (px)
        self.ui = ui


    def toggle_pause(self):
        # Why: keeps previous time_scale when unpausing.
        if not self.paused:
            self._prev_time_scale = self.time_scale
            self.time_scale = 0.0
            self.paused = True
        else:
            self.time_scale = self._prev_time_scale if self._prev_time_scale > 0 else 1.0
            self.paused = False
