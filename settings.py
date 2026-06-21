"""Shared settings for Blind Goat Hunt.

All gameplay constants live here so the demo stays easy to tune.
The project intentionally keeps dimensions and object lists deterministic
instead of loading external assets.
"""

WINDOW_WIDTH = 900
WINDOW_HEIGHT = 620
FPS = 60

MAP_MARGIN = 28
MAP_RECT = (MAP_MARGIN, MAP_MARGIN, WINDOW_WIDTH - MAP_MARGIN * 2, WINDOW_HEIGHT - MAP_MARGIN * 2)

HUNTER_SPEED = 240
GOAT_SPEED = HUNTER_SPEED / 3
# Demo-friendly default: goat moves with arrow keys, while SPACE only marks
# "making_noise" for the future audio/DSP integration. Set this to True if you
# want to restore the original mic-gated movement rule.
GOAT_REQUIRES_NOISE_TO_MOVE = False

PLAYER_RADIUS = 16
CATCH_RADIUS = 28
VISION_RADIUS = 38
GAME_DURATION = 60.0

NOISE_DISPLAY_SECONDS = 0.8
GOAT_OBSTACLE_NOISE_COOLDOWN = 0.8
GOAT_IDLE_NOISE_AFTER = 2.0
HUNTER_SCAN_INTERVAL = 3.0
TRAP_NOISE_COOLDOWN = 1.0

SERVER_TICK_RATE = 60
CLIENT_SEND_RATE = 30
NETWORK_TIMEOUT_SECONDS = 5.0

INPUT_STALE_SECONDS = 0.35
PACKET_SIZE = 8192

HUNTER_START = (120, WINDOW_HEIGHT / 2)
GOAT_START = (WINDOW_WIDTH - 130, WINDOW_HEIGHT / 2)

# Rectangles are (x, y, width, height). Obstacles are short bars by design:
# they shape movement for the goat without creating a maze.
OBSTACLES = [
    (175, 115, 120, 22),
    (385, 90, 26, 112),
    (595, 130, 132, 22),
    (105, 265, 118, 24),
    (310, 260, 135, 24),
    (520, 260, 25, 118),
    (675, 310, 112, 24),
    (185, 455, 128, 22),
    (420, 465, 126, 24),
    (640, 455, 26, 95),
]

# Traps are fake audio objects. The server emits a noise event when the goat
# steps on one, and the audio team can replace this later with real DSP input.
TRAPS = [
    {"kind": "bush", "x": 250, "y": 205, "radius": 15},
    {"kind": "can", "x": 585, "y": 210, "radius": 12},
    {"kind": "leaves", "x": 735, "y": 180, "radius": 14},
    {"kind": "bush", "x": 160, "y": 395, "radius": 16},
    {"kind": "can", "x": 470, "y": 375, "radius": 12},
    {"kind": "leaves", "x": 735, "y": 475, "radius": 14},
]

COLORS = {
    "background": (15, 18, 20),
    "map_floor": (31, 37, 39),
    "grid": (49, 57, 59),
    "border": (125, 143, 139),
    "text": (229, 235, 232),
    "muted_text": (159, 170, 166),
    "hunter": (244, 210, 128),
    "hunter_dark": (40, 36, 36),
    "goat": (229, 229, 218),
    "goat_dark": (58, 62, 55),
    "horn": (199, 184, 139),
    "obstacle": (103, 92, 80),
    "obstacle_edge": (154, 137, 112),
    "trap_bush": (62, 135, 79),
    "trap_can": (158, 167, 177),
    "trap_leaves": (178, 131, 70),
    "noise": (255, 44, 54),
    "overlay": (3, 5, 6),
    "success": (94, 210, 132),
    "danger": (255, 95, 95),
}
