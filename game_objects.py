"""Pygame geometry, collision, and drawing helpers for Blind Goat Hunt."""

from __future__ import annotations

import math
from typing import Iterable

import pygame

from settings import (
    COLORS,
    MAP_RECT,
    OBSTACLES,
    PLAYER_RADIUS,
    TRAPS,
    VISION_RADIUS,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
)


def map_rect() -> pygame.Rect:
    return pygame.Rect(MAP_RECT)


def obstacle_rects() -> list[pygame.Rect]:
    return [pygame.Rect(rect) for rect in OBSTACLES]


def clamp_to_map(x: float, y: float, radius: int = PLAYER_RADIUS) -> tuple[float, float]:
    bounds = map_rect()
    return (
        max(bounds.left + radius, min(bounds.right - radius, x)),
        max(bounds.top + radius, min(bounds.bottom - radius, y)),
    )


def collides_with_obstacle(x: float, y: float, radius: int = PLAYER_RADIUS) -> bool:
    return any(rect.collidepoint(x, y) or circle_rect_collision(x, y, radius, rect) for rect in obstacle_rects())


def circle_rect_collision(cx: float, cy: float, radius: float, rect: pygame.Rect) -> bool:
    nearest_x = max(rect.left, min(cx, rect.right))
    nearest_y = max(rect.top, min(cy, rect.bottom))
    return (cx - nearest_x) ** 2 + (cy - nearest_y) ** 2 <= radius**2


def move_with_obstacles(
    x: float,
    y: float,
    dx: float,
    dy: float,
    speed: float,
    dt: float,
    *,
    can_pass_obstacles: bool,
) -> tuple[float, float, bool]:
    """Move a circular player and report whether an obstacle blocked the move."""
    if dx == 0 and dy == 0:
        return x, y, False

    length = math.hypot(dx, dy)
    vx = dx / length * speed * dt
    vy = dy / length * speed * dt

    blocked = False
    new_x, new_y = clamp_to_map(x + vx, y + vy)

    if can_pass_obstacles:
        return new_x, new_y, False

    if not collides_with_obstacle(new_x, new_y):
        return new_x, new_y, False

    blocked = True

    # Axis-separated movement gives the goat a simple slide along walls.
    axis_x, axis_y = clamp_to_map(x + vx, y)
    if not collides_with_obstacle(axis_x, axis_y):
        x = axis_x

    axis_x, axis_y = clamp_to_map(x, y + vy)
    if not collides_with_obstacle(axis_x, axis_y):
        y = axis_y

    return x, y, blocked


def distance(a: tuple[float, float], b: tuple[float, float]) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def point_visible_to_hunter(hunter: dict[str, float], x: float, y: float, extra: float = 0) -> bool:
    return distance((hunter["x"], hunter["y"]), (x, y)) <= VISION_RADIUS + extra


def rect_visible_to_hunter(hunter: dict[str, float], rect: pygame.Rect) -> bool:
    return circle_rect_collision(hunter["x"], hunter["y"], VISION_RADIUS, rect)


def trap_visible_to_hunter(hunter: dict[str, float], trap: dict[str, float]) -> bool:
    return point_visible_to_hunter(hunter, trap["x"], trap["y"], trap.get("radius", 0))


def draw_map_base(surface: pygame.Surface, *, show_grid: bool = True) -> None:
    surface.fill(COLORS["background"])
    bounds = map_rect()
    pygame.draw.rect(surface, COLORS["map_floor"], bounds)
    if show_grid:
        draw_grid(surface, bounds)
    pygame.draw.rect(surface, COLORS["border"], bounds, 3)


def draw_grid(surface: pygame.Surface, bounds: pygame.Rect) -> None:
    step = 40
    for x in range(bounds.left + step, bounds.right, step):
        pygame.draw.line(surface, COLORS["grid"], (x, bounds.top), (x, bounds.bottom), 1)
    for y in range(bounds.top + step, bounds.bottom, step):
        pygame.draw.line(surface, COLORS["grid"], (bounds.left, y), (bounds.right, y), 1)


def draw_obstacles(surface: pygame.Surface, rects: Iterable[pygame.Rect] | None = None) -> None:
    for rect in rects if rects is not None else obstacle_rects():
        pygame.draw.rect(surface, COLORS["obstacle"], rect, border_radius=3)
        pygame.draw.rect(surface, COLORS["obstacle_edge"], rect, 2, border_radius=3)


def draw_traps(surface: pygame.Surface, traps: Iterable[dict[str, float]] | None = None) -> None:
    for trap in traps if traps is not None else TRAPS:
        x, y = int(trap["x"]), int(trap["y"])
        radius = int(trap.get("radius", 12))
        kind = trap.get("kind", "bush")

        if kind == "can":
            rect = pygame.Rect(x - 8, y - 5, 16, 10)
            pygame.draw.rect(surface, COLORS["trap_can"], rect, border_radius=3)
            pygame.draw.line(surface, (230, 236, 240), (rect.left + 3, rect.centery), (rect.right - 3, rect.centery), 1)
        elif kind == "leaves":
            color = COLORS["trap_leaves"]
            points = [(x, y - radius), (x + radius, y), (x + 3, y + radius), (x - radius, y + 3)]
            pygame.draw.polygon(surface, color, points)
            pygame.draw.line(surface, (105, 76, 42), (x - 4, y - 7), (x + 5, y + 8), 2)
        else:
            pygame.draw.circle(surface, COLORS["trap_bush"], (x, y), radius)
            pygame.draw.circle(surface, (92, 171, 98), (x - 5, y - 4), max(4, radius // 3))
            pygame.draw.circle(surface, (44, 107, 61), (x + 5, y + 4), max(4, radius // 3))


def draw_hunter(surface: pygame.Surface, x: float, y: float) -> None:
    center = (int(x), int(y))
    pygame.draw.circle(surface, COLORS["hunter"], center, PLAYER_RADIUS)
    pygame.draw.circle(surface, (101, 73, 48), center, PLAYER_RADIUS, 2)

    blindfold = pygame.Rect(center[0] - 15, center[1] - 5, 30, 9)
    pygame.draw.rect(surface, COLORS["hunter_dark"], blindfold, border_radius=4)
    pygame.draw.line(surface, COLORS["hunter_dark"], (center[0] - 19, center[1] - 3), (center[0] - 14, center[1] + 2), 2)
    pygame.draw.line(surface, COLORS["hunter_dark"], (center[0] + 14, center[1] + 2), (center[0] + 19, center[1] - 3), 2)
    pygame.draw.circle(surface, (229, 171, 112), (center[0], center[1] + 7), 3)


def draw_goat(surface: pygame.Surface, x: float, y: float) -> None:
    center = (int(x), int(y))
    left_horn = [(center[0] - 11, center[1] - 13), (center[0] - 20, center[1] - 24), (center[0] - 15, center[1] - 10)]
    right_horn = [(center[0] + 11, center[1] - 13), (center[0] + 20, center[1] - 24), (center[0] + 15, center[1] - 10)]
    pygame.draw.polygon(surface, COLORS["horn"], left_horn)
    pygame.draw.polygon(surface, COLORS["horn"], right_horn)
    pygame.draw.circle(surface, COLORS["goat"], center, PLAYER_RADIUS)
    pygame.draw.circle(surface, COLORS["goat_dark"], center, PLAYER_RADIUS, 2)
    pygame.draw.circle(surface, COLORS["goat_dark"], (center[0] - 6, center[1] - 2), 2)
    pygame.draw.circle(surface, COLORS["goat_dark"], (center[0] + 6, center[1] - 2), 2)
    pygame.draw.line(surface, COLORS["goat_dark"], (center[0], center[1] + 2), (center[0], center[1] + 8), 2)
    pygame.draw.arc(surface, COLORS["goat_dark"], (center[0] - 6, center[1] + 3, 12, 9), 0, math.pi, 2)


def draw_noise_signal(surface: pygame.Surface, x: float, y: float, progress: float) -> None:
    """Draw a noise ping that expands and fades over its lifetime.

    progress runs 0.0 (just appeared) -> 1.0 (about to vanish).
    """
    progress = max(0.0, min(1.0, progress))
    fade = 1.0 - progress

    ring_radius = int(8 + 26 * progress)  # ring grows outward like a sound wave
    core_alpha = int(255 * fade)
    ring_alpha = int(170 * fade)

    size = (ring_radius + 4) * 2
    pulse = pygame.Surface((size, size), pygame.SRCALPHA)
    center = (size // 2, size // 2)
    pygame.draw.circle(pulse, (*COLORS["noise"], ring_alpha), center, ring_radius, 3)
    pygame.draw.circle(pulse, (*COLORS["noise"], core_alpha), center, 7)
    surface.blit(pulse, (int(x) - center[0], int(y) - center[1]))


# Cached surfaces for the hunter "spotlight" darkness. Neither the dark overlay
# nor the soft-edged vision gradient changes shape, so we build them once and
# only reposition the gradient each frame (no per-frame allocations).
_DARKNESS_ALPHA = 238
_VISION_FEATHER = 26  # px over which the vision edge fades out, beyond VISION_RADIUS

_darkness_overlay: pygame.Surface | None = None
_vision_gradient: pygame.Surface | None = None


def _get_vision_gradient() -> pygame.Surface:
    """Square mask: fully clear out to VISION_RADIUS, then fading to dark.

    Corners are kept fully dark so the square blends seamlessly into the
    surrounding overlay when combined with BLEND_RGBA_MIN.
    """
    global _vision_gradient
    if _vision_gradient is not None:
        return _vision_gradient

    overlay_rgb = COLORS["overlay"]
    outer = VISION_RADIUS + _VISION_FEATHER
    size = outer * 2
    grad = pygame.Surface((size, size), pygame.SRCALPHA)
    grad.fill((*overlay_rgb, _DARKNESS_ALPHA))

    # Paint concentric circles from the outer edge inward. Each ring keeps the
    # alpha of the largest circle that reached it, producing a smooth falloff:
    # opaque at the edge -> fully transparent inside VISION_RADIUS.
    for r in range(outer, 0, -1):
        if r <= VISION_RADIUS:
            alpha = 0
        else:
            t = (r - VISION_RADIUS) / _VISION_FEATHER  # 0 -> 1 across the feather
            alpha = int(_DARKNESS_ALPHA * (t ** 1.5))
        pygame.draw.circle(grad, (*overlay_rgb, alpha), (outer, outer), r)

    _vision_gradient = grad
    return grad


def apply_hunter_darkness(surface: pygame.Surface, hunter_x: float, hunter_y: float) -> None:
    """Darken the hunter screen, leaving a soft-edged circular vision window."""
    global _darkness_overlay
    if _darkness_overlay is None:
        _darkness_overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)

    overlay = _darkness_overlay
    overlay.fill((*COLORS["overlay"], _DARKNESS_ALPHA))

    grad = _get_vision_gradient()
    outer = VISION_RADIUS + _VISION_FEATHER
    # BLEND_RGBA_MIN keeps the overlay colour but lowers its alpha to match the
    # gradient inside the circle, punching a soft hole without affecting corners.
    overlay.blit(
        grad,
        (int(hunter_x) - outer, int(hunter_y) - outer),
        special_flags=pygame.BLEND_RGBA_MIN,
    )
    surface.blit(overlay, (0, 0))


def draw_hud(
    surface: pygame.Surface,
    font: pygame.font.Font,
    small_font: pygame.font.Font,
    *,
    role: str,
    time_left: float,
    winner: str | None,
    connected: bool,
    waiting_for_players: bool,
    name: str = "",
) -> None:
    seconds = max(0, int(math.ceil(time_left)))
    timer_color = COLORS["danger"] if seconds <= 10 else COLORS["text"]
    timer = font.render(f"Time: {seconds:02d}", True, timer_color)
    timer_x, timer_y = 36, 12
    surface.blit(timer, (timer_x, timer_y))

    # Place the role label right after the timer and vertically centred on it,
    # instead of a hard-coded x/y that drifts out of alignment.
    role_label = "Hunter" if role == "hunter" else "Goat"
    if name:
        role_label = f"{role_label} · {name}"
    role_text = small_font.render(role_label, True, COLORS["muted_text"])
    role_x = timer_x + timer.get_width() + 16
    role_y = timer_y + (timer.get_height() - role_text.get_height()) // 2
    surface.blit(role_text, (role_x, role_y))

    if role == "hunter":
        help_text = "WASD to move   |   R to reset"
    else:
        help_text = "Arrow keys / WASD to move   |   R to reset"
    hint = small_font.render(help_text, True, COLORS["text"])
    surface.blit(hint, (36, WINDOW_HEIGHT - 26))

    if not connected:
        draw_banner(surface, font, "Waiting for server...", COLORS["danger"])
    elif waiting_for_players:
        draw_banner(surface, font, "Waiting for both players...", COLORS["muted_text"])

    if winner is not None:
        if winner == "hunter":
            message = "Hunter caught the goat! Press R to reset"
            color = COLORS["success"] if role == "hunter" else COLORS["danger"]
        else:
            message = "Time ran out. Goat wins! Press R to reset"
            color = COLORS["success"] if role == "goat" else COLORS["danger"]
        draw_banner(surface, font, message, color, y=WINDOW_HEIGHT // 2 - 20)


def draw_banner(surface: pygame.Surface, font: pygame.font.Font, text: str, color: tuple[int, int, int], y: int = 54) -> None:
    label = font.render(text, True, color)
    padding = 14
    rect = label.get_rect(center=(WINDOW_WIDTH // 2, y))
    bg = rect.inflate(padding * 2, 12)
    banner = pygame.Surface(bg.size, pygame.SRCALPHA)
    banner.fill((0, 0, 0, 150))
    surface.blit(banner, bg)
    surface.blit(label, rect)
