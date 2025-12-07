# =========================
# file: game.py
# =========================
import pygame
import const
from game_context import GameContext
from scene_manager import SceneManager
from scenes.tank_scene import TankScene
from config import load_config
from render.audio_manager import AudioManager

class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Fish SIM")

        self.settings = load_config()
        w = self.settings["screen_width"]
        h = self.settings["screen_height"]
        fullscreen = self.settings["fullscreen"]

        flags = pygame.RESIZABLE
        if fullscreen:
            flags |= pygame.FULLSCREEN
        self.screen = pygame.display.set_mode((w, h), flags)
        self.clock = pygame.time.Clock()

        self.context = GameContext()
        self.context.assets.load_folder("assets/sprites")
        self.context.audio = AudioManager(self.settings)

        # Scene
        initial_scene = TankScene(self.context, self.screen)
        self.scene_manager = SceneManager(initial_scene)

        # Initial resize (so tank lays out once)
        sw, sh = self.screen.get_size()
        self.context.new_screen_w = sw
        self.context.new_screen_h = sh
        self.context.needs_resize = True

        self.dt = 1.0 / const.FPS
        self.accumulator = 0.0

    def run(self):
        while self.context.running:
            frame_time = self.clock.tick(const.FPS) / 1000.0
            self.context.fps = self.clock.get_fps()
            self.accumulator += frame_time

            for event in pygame.event.get():
                # --- FIX: honor OS window close (❌) ---
                if event.type == pygame.QUIT:
                    self.context.running = False
                    continue  # no further dispatch

                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    if self.context.debug_escape_quit:
                        self.context.running = False

                if event.type == pygame.VIDEORESIZE:
                    self.screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                    if hasattr(self.scene_manager.current_scene, "set_screen"):
                        self.scene_manager.current_scene.set_screen(self.screen)
                    self.context.new_screen_w = int(event.w)
                    self.context.new_screen_h = int(event.h)
                    self.context.needs_resize = True

                # Route once to the active scene
                self.scene_manager.handle_event(event)

            while self.accumulator >= self.dt:
                self.scene_manager.update(self.dt * self.context.time_scale)
                self.accumulator -= self.dt

            self.screen.fill(const.BG_COLOR)

            self.scene_manager.render(self.screen)
            pygame.display.flip()

        pygame.quit()
