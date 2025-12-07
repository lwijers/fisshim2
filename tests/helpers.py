# tests/helpers.py
from world import World
from game_context import GameContext

def make_world():
    return World()

def make_context(**overrides):
    ctx = GameContext()
    # keep parity with your conftest defaults
    if "logical_w" in overrides:
        ctx.logical_tank_w = int(overrides["logical_w"])
    if "logical_h" in overrides:
        ctx.logical_tank_h = int(overrides["logical_h"])
    for k, v in overrides.items():
        setattr(ctx, k, v)
    return ctx
