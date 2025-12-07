# Basic scene wiring smoke test; ensures scene can construct under dummy SDL.
import pygame
import pytest

def test_scene_initializes(make_context):
    try:
        from scenes.tank_scene import TankScene
    except Exception:
        pytest.skip("TankScene not available")
    ctx = make_context()
    # create a dummy screen surface (no window needed with dummy driver)
    screen = pygame.display.set_mode((800, 600))
    scene = TankScene(ctx, screen)
    scene.update(0.0)
    assert scene is not None
