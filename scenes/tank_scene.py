# scenes/tank_scene.py
import random
import pygame
from scenes.base_scene import BaseScene
from world import World

# Core/tank
from ecs.components.core.position_component import Position
from ecs.components.core.bounds_component import Bounds
from ecs.components.core.tank_style_component import TankStyle
from ecs.components.core.tank_label_component import TankLabel
from ecs.components.core.tank_component import Tank
from ecs.components.core.tank_ref_component import TankRef
from ecs.components.core.sprite_component import Sprite

# Fish core
from ecs.components.fish.species_component import Species
from ecs.components.fish.age_component import Age
from ecs.components.fish.health_component import Health
from ecs.components.fish.hunger_component import Hunger
from ecs.components.fish.breeding_component import Breeding

# Motion/AI (needed for movement)
from ecs.components.core.velocity_component import Velocity
from ecs.components.fish.motion_component import MotionParams
from ecs.components.fish.target_intent_component import TargetIntent
from ecs.components.fish.steering_intent_component import SteeringIntent
from ecs.components.fish.speed_intent_component import SpeedIntent
from ecs.components.fish.brain_component import Brain
from ecs.components.fish.behavior_tuning import BehaviorTuning

# Input/UI
from ecs.systems.ui.input_router import InputRouter
from ecs.systems.ui.keyboard_system import KeyboardSystem
from ecs.systems.ui.mouse_system import MouseSystem
from ecs.systems.ui.placement_system import PlacementSystem

# Update systems
from ecs.systems.core.resize_system import ResizeSystem
from ecs.systems.core.movement_system import MovementSystem
from ecs.systems.core.collision_system import CollisionSystem
from ecs.systems.core.avoidance_system import AvoidanceSystem
from ecs.systems.physics.gravity_system import GravitySystem
from ecs.systems.gameplay.hunger_system import HungerSystem
from ecs.systems.gameplay.health_system import HealthSystem
from ecs.systems.gameplay.aging_system import AgingSystem

# Rendering
from ecs.systems.rendering.tank_render_system import TankRenderSystem
from ecs.systems.rendering.sprite_render_system import SpriteRenderSystem
from ecs.systems.rendering.fish_overlay_system import FishOverlaySystem
from ecs.systems.ui.debug.debug_overlay_system import DebugOverlaySystem
from ecs.systems.ui.debug.debug_menu import DebugMenu
from ecs.systems.ui.ui_toolbar_system import UIToolbarSystem
from ecs.systems.ui.cursor_system import CursorSystem
from ecs.systems.ui.fish_window_system import FishWindowSystem
from ecs.systems.ui.fish_inspector_system import FishInspectorSystem
from ecs.systems.ui.widgets.panel_manager_system import PanelManagerSystem
# AI
from ecs.systems.ai.behavior_system import BehaviorSystem
from ecs.systems.ai.state_override_system import StateOverrideSystem
from ecs.systems.ai.state_transition_system import StateTransitionSystem

# Breeding
from ecs.systems.gameplay.population_guard import PopulationGuard

# Factories
from ecs.factories.fish_factory import create_fish


class TankScene(BaseScene):
    """
    Scene wiring:
      - Events → InputRouter → (KeyboardSystem / MouseSystem)
      - PlacementSystem spawns pellets/eggs each update
      - Breeding: PopulationGuard → Eligibility → MateSearch → Courtship
      - AI: Behavior → Override → Transition (then movement/collision)
    """
    def __init__(self, context, screen):
        super().__init__()
        self.context = context
        self.screen = screen
        self.world = World()

        # ---------- Input ----------
        self.keyboard = KeyboardSystem(context)
        self.mouse = MouseSystem(context, screen, context.assets)
        self.placement = PlacementSystem(context)
        self.input_router = InputRouter(self.keyboard, self.mouse)
        self.mouse.set_placement(self.placement)
        self.context.spawn_egg = self.placement.spawn_egg_at

        # ---------- Systems (order matters) ----------
        self.world.add_system(ResizeSystem(context), phase="update")

        # Gameplay basics
        self.world.add_system(HungerSystem(), phase="update")
        self.world.add_system(HealthSystem(), phase="update")
        self.world.add_system(AgingSystem(context), phase="update")

        # Breeding loop
        self.population_guard = PopulationGuard(context)
        self.world.add_system(self.population_guard, phase="update")

        # AI “sandwich” (Behavior is driven outside world.update to pass planned states)
        self.behavior = BehaviorSystem(context)
        self.override = StateOverrideSystem()
        self.transition = StateTransitionSystem(context, self.behavior)

        # Motion & physics
        self.world.add_system(AvoidanceSystem(context), phase="update")
        self.world.add_system(MovementSystem(context), phase="update")
        self.world.add_system(CollisionSystem(context), phase="update")
        self.world.add_system(GravitySystem(context), phase="update")

        # Spawners late
        self.world.add_system(self.placement, phase="update")

        # Rendering
        self.tank_renderer = TankRenderSystem(screen, context.assets, context)
        self.sprite_renderer = SpriteRenderSystem(screen, context.assets, context)
        self.fish_overlay = FishOverlaySystem(screen, context.assets, context)
        self.debug_overlay = DebugOverlaySystem(screen, context)
        self.ui_toolbar = UIToolbarSystem(screen, context.assets, context)
        self.cursor_system = CursorSystem(screen, context.assets, context)
        self.fish_window = FishWindowSystem(screen, context.assets, context)
        self.fish_inspector = FishInspectorSystem(screen, context.assets, context)
        self.panel_manager = PanelManagerSystem(screen, context.assets, context)

        self.world.add_system(self.tank_renderer, phase="render")
        self.world.add_system(self.sprite_renderer, phase="render")
        self.world.add_system(self.fish_overlay, phase="render")
        self.world.add_system(self.debug_overlay, phase="render")
        self.world.add_system(DebugMenu(screen, context), phase="render")
        self.world.add_system(self.ui_toolbar, phase="render")
        self.world.add_system(self.cursor_system, phase="render")
        self.world.add_system(self.fish_window, phase="render")
        self.world.add_system(self.fish_inspector, phase="render")
        self.world.add_system(self.panel_manager, phase="render")

        # ---------- Tank ----------
        tank = self.world.create_entity()
        self.tank_entity = tank
        self.world.add_component(tank, Tank())
        self.world.add_component(tank, Position(0, 0))
        self.world.add_component(tank, Bounds(1, 1))
        self.world.add_component(tank, TankStyle())
        self.world.add_component(tank, TankLabel(text="My Tank"))
        self.keyboard.set_tank(tank)
        self.mouse.set_tank(tank)
        self.mouse.set_panel_manager(self.panel_manager)
        self.mouse.set_world_ref(self.world)
        self.placement.set_tank(tank)
        self.tank_entity = tank

        # Spawn from config
        for sid, data in (self.context.species_config or {}).items():
            x = random.uniform(0, self.context.logical_tank_w)
            y = random.uniform(0, self.context.logical_tank_h)
            create_fish(self.world, self.context, tank, sid, data, x, y)

        # EXTRA: adults for breeding + movement debug
        self._spawn_debug_adults(tank)

        # Initial resize once
        if not self.context.needs_resize:
            sw, sh = self.screen.get_size()
            self.context.new_screen_w = sw
            self.context.new_screen_h = sh
            self.context.needs_resize = True

        self.world.update(0.0)

    # ---------- Scene API ----------
    def handle_event(self, event):
        self.input_router.handle_event(event)
        if event.type == pygame.VIDEORESIZE:
            self.context.new_screen_w = int(event.w)
            self.context.new_screen_h = int(event.h)
            self.context.needs_resize = True

    def update(self, dt):
        # Drive AI pipeline around world.update so intents are fresh
        proposed = self.behavior.update(self.world, dt)
        overridden = self.override.update(self.world, proposed)
        self.transition.update(self.world, overridden, dt)

        # Wire world ref for keyboard ops
        self.keyboard.set_world_ref(self.world)
        self.keyboard.update(self.world, dt)

        self.mouse.update(self.world, dt)
        self.world.update(dt)

    def render(self, screen):
        self.world.render()

    def set_screen(self, new_screen):
        self.screen = new_screen
        self.mouse.screen = new_screen
        self.tank_renderer.screen = new_screen
        self.sprite_renderer.screen = new_screen
        self.fish_overlay.screen = new_screen
        self.debug_overlay.screen = new_screen
        self.ui_toolbar.screen = new_screen
        self.fish_inspector.screen = new_screen
        self.panel_manager.screen = new_screen

    # ---------- Helpers ----------
    def _spawn_debug_adults(self, tank):
        """Adult fish with full movement + AI + breeding toggle_on."""
        cfg = self.context.species_config.get("goldfish", {"sprite": "goldfish", "width": 60, "height": 40})
        W = float(self.context.logical_tank_w)
        H = float(self.context.logical_tank_h)

        def rand_target():
            margin = 40
            return (
                random.uniform(margin, max(margin, W - margin)),
                random.uniform(margin, max(margin, H - margin)),
            )

        for i in range(6):
            x = (i % 3) * (W / 3.5) + 80
            y = (i // 3) * (H / 3.0) + 120
            tx, ty = rand_target()
            e = self.world.create_entity()
            self.world.add_component(e, TankRef(tank))
            self.world.add_component(e, Position(x, y))
            self.world.add_component(e, Sprite(cfg.get("sprite", "goldfish"), cfg.get("width", 60), cfg.get("height", 40)))
            self.world.add_component(e, Species("goldfish", "Goldfish", base_speed=150.0))

            # Movement + AI essentials (missing before → fish were static)
            self.world.add_component(e, Velocity(0.0, 0.0))
            self.world.add_component(e, MotionParams(max_speed=150.0, acceleration=220.0, turn_speed=8.0))
            self.world.add_component(e, TargetIntent(tx, ty))
            self.world.add_component(e, SpeedIntent(0.0))
            self.world.add_component(e, SteeringIntent())
            self.world.add_component(e, Brain(state="Cruise"))
            self.world.add_component(e, BehaviorTuning({
                "cruise_min_time": 1.0,
                "cruise_max_time": 2.0,
                "cruise_arrival_radius": 40.0,
                "cruise_speed_factor": 0.6,
                "transition_to_idle_chance": 0.05,
                "idle_min_time": 0.6,
                "idle_max_time": 1.4,
                "idle_speed_factor": 0.08,
                "idle_bob_amplitude": 18.0,
                "idle_bob_frequency": 0.8,
                "transition_to_cruise_chance": 0.25,
                "food_detect_radius": 250.0,
                "food_seek_threshold": 0.80,
                "look_for_food_speed_factor": 1.0,
                "chase_food_speed_factor": 1.00,
                "food_nutrition": 40.0,
                "noise": 0.05,
                "mouth_radius_factor": 0.40,
                "eat_extra_margin": 8.0,
            }))

            # Life state + breeding
            self.world.add_component(e, Age(age=0.0, lifespan=200.0, stage="Adult"))
            self.world.add_component(e, Health(value=100.0, max_value=100.0))
            self.world.add_component(e, Hunger(hunger=100.0, hunger_rate=0.1, hunger_max=100.0))
            self.world.add_component(e, Breeding(toggle_on=True))
