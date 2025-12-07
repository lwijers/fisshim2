"""
const.py
Engine-wide constants and debug toggles.
User settings should NOT be stored here.
"""
# === Display & Timing ===
FPS = 60
TICK_TIME = 1.0 / FPS

# === Colors ===
WHITE        = (255, 255, 255)
BLACK        = (0, 0, 0)
LIGHT_GREY   = (200, 200, 200)
DARK_GREY    = (50, 50, 50)
TRANSPARENT  = (0, 0, 0, 0)
COLORKEY     = (255, 0, 255)
BG_COLOR     = (40, 90, 160)

# === Render Layers ===
LAYER_BG       = 0
LAYER_TERRAIN  = 1
LAYER_ENTITIES = 2
LAYER_UI       = 3

# === Debug Flags (engine-side only; NOT user-configurable) ===
DEBUG_SHOW_BEHAVIOR_LABELS   = False
DEBUG_SHOW_STATS_BARS        = False

# Target lines (fish → its current target point)
DEBUG_SHOW_TARGET_LINES      = False

# Velocity & avoidance
DEBUG_SHOW_VELOCITY_ARROWS   = False
DEBUG_SHOW_AVOIDANCE_ARROWS  = False

# Food-specific debug
DEBUG_SHOW_FISH_VISION       = False   # cyan circles around fish (vision)
DEBUG_SHOW_PELLET_RADIUS     = False   # blue circles around pellets (sprite radius)
DEBUG_SHOW_FOOD_LINKS        = False   # orange line mouth → targeted pellet
DEBUG_SHOW_SPRITE_BORDER     = False

# Escape quits game in debug mode
DEBUG_ESCAPE_QUIT = True
