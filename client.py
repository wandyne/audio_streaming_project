"""Pygame client for Blind Goat Hunt.

Run one client per player:
    python client.py --role hunter --server SERVER_IP --port 5000
    python client.py --role goat --server SERVER_IP --port 5000
"""

from __future__ import annotations
from voice_engine import VoiceEngine

import argparse
import time
from typing import Any

import pygame

from game_objects import (
    apply_hunter_darkness,
    draw_goat,
    draw_hud,
    draw_hunter,
    draw_map_base,
    draw_noise_signal,
    draw_obstacles,
    draw_traps,
    obstacle_rects,
    point_visible_to_hunter,
    rect_visible_to_hunter,
    trap_visible_to_hunter,
)
from network import create_udp_socket, recv_json, send_json
from settings import (
    CLIENT_SEND_RATE,
    COLORS,
    GAME_DURATION,
    GOAT_REQUIRES_NOISE_TO_MOVE,
    GOAT_START,
    HUNTER_START,
    NETWORK_TIMEOUT_SECONDS,
    NOISE_DISPLAY_SECONDS,
    TRAPS,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
)


VALID_ROLES = {"hunter", "goat"}


class GameClient:
    def __init__(self, role: str, server: str, port: int, name: str = "") -> None:
        self.role = role
        self.name = name
        self.server_address = (server, port)
        self.sock = create_udp_socket()

        self.state: dict[str, Any] = {
            "hunter": {"x": float(HUNTER_START[0]), "y": float(HUNTER_START[1])},
            "goat": {"x": float(GOAT_START[0]), "y": float(GOAT_START[1])},
            "time_left": GAME_DURATION,
            "winner": None,
            "noise_event": {"active": False},
            "waiting_for_players": True,
        }

        self.last_state_at = 0.0
        self.last_send_at = 0.0
        self.reset_requested = False
        self.last_noise_id: int | None = None
        self.visible_noises: list[dict[str, Any]] = []

        pygame.init()
        caption = f"Blind Goat Hunt - {role.title()}"
        if name:
            caption += f" ({name})"
        pygame.display.set_caption(caption)
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.clock = pygame.time.Clock()
        # Voice Engine

        voice_port = port + 100

        self.voice = VoiceEngine(

            local_ip="0.0.0.0",

            local_port=voice_port,

            remote_ip=server,

            remote_port=voice_port,

        )

        self.voice.start()

        self.font = pygame.font.SysFont(None, 30)
        self.small_font = pygame.font.SysFont(None, 22)

    def run(self) -> None:
        running = True
        while running:
            now = time.monotonic()
            dt = self.clock.tick(60) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                    self.reset_requested = True

            input_state = self.collect_input()
            self.send_input(input_state, now)
            self.receive_state(now)
            self.render(input_state, dt, now)

        self.voice.stop()

        pygame.quit()

    def collect_input(self) -> dict[str, Any]:
        keys = pygame.key.get_pressed()
        dx = 0
        dy = 0
        hunter = self.state["hunter"]

        goat = self.state["goat"]

        if self.role == "hunter":

            listener_position = (

                hunter["x"],

                hunter["y"],

            )

            source_position = (

                goat["x"],

                goat["y"],

            )

        else:

            listener_position = (

                goat["x"],

                goat["y"],

            )

            source_position = (

                hunter["x"],

                hunter["y"],

            )
       
        making_noise = self.voice.update(
            listener_position,
            source_position,
        )

        if self.role == "hunter":
            dx = int(keys[pygame.K_d]) - int(keys[pygame.K_a])
            dy = int(keys[pygame.K_s]) - int(keys[pygame.K_w])
        else:
            dx = (int(keys[pygame.K_RIGHT]) or int(keys[pygame.K_d])) - (
                int(keys[pygame.K_LEFT]) or int(keys[pygame.K_a])
            )
            dy = (int(keys[pygame.K_DOWN]) or int(keys[pygame.K_s])) - (
                int(keys[pygame.K_UP]) or int(keys[pygame.K_w])
            )

        requested_direction = dx != 0 or dy != 0
        if self.role == "hunter":
            actually_moving = requested_direction
        else:
            actually_moving = requested_direction and (making_noise or not GOAT_REQUIRES_NOISE_TO_MOVE)

        return {
            "dx": dx,
            "dy": dy,
            "moving": actually_moving,
            "making_noise": making_noise,
        }

    def send_input(self, input_state: dict[str, Any], now: float) -> None:
        if now - self.last_send_at < 1.0 / CLIENT_SEND_RATE:
            return

        message = {
            "type": "input",
            "role": self.role,
            "dx": input_state["dx"],
            "dy": input_state["dy"],
            "moving": input_state["moving"],
            "making_noise": input_state["making_noise"],
        }

        if self.reset_requested:
            message["reset"] = True
            self.reset_requested = False

        send_json(self.sock, message, self.server_address)
        self.last_send_at = now

    def receive_state(self, now: float) -> None:
        for message, _address in recv_json(self.sock):
            if message.get("type") != "state":
                continue

            self.state.update(message)
            self.last_state_at = now
            self.capture_new_noise(now)

    def capture_new_noise(self, now: float) -> None:
        if self.role != "hunter":
            return

        noise = self.state.get("noise_event") or {}
        if not noise.get("active"):
            return

        noise_id = noise.get("id")
        if noise_id == self.last_noise_id:
            return

        self.last_noise_id = noise_id
        self.visible_noises.append(
            {
                "id": noise_id,
                "x": float(noise.get("x", 0)),
                "y": float(noise.get("y", 0)),
                "reason": noise.get("reason", "noise"),
                "received_at": now,
            }
        )

    def render(self, input_state: dict[str, Any], _dt: float, now: float) -> None:
        connected = now - self.last_state_at <= NETWORK_TIMEOUT_SECONDS
        if self.role == "hunter":
            self.render_hunter(now, connected, input_state)
        else:
            self.render_goat(now, connected, input_state)

        pygame.display.flip()

    def render_hunter(self, now: float, connected: bool, input_state: dict[str, Any]) -> None:
        hunter = self.state["hunter"]
        goat = self.state["goat"]

        # Draw the actual world, then cover everything except the vision circle.
        draw_map_base(self.screen, show_grid=True)

        visible_obstacles = [rect for rect in obstacle_rects() if rect_visible_to_hunter(hunter, rect)]
        visible_traps = [trap for trap in TRAPS if trap_visible_to_hunter(hunter, trap)]
        draw_obstacles(self.screen, visible_obstacles)
        draw_traps(self.screen, visible_traps)

        if point_visible_to_hunter(hunter, goat["x"], goat["y"], extra=16):
            draw_goat(self.screen, goat["x"], goat["y"])
        draw_hunter(self.screen, hunter["x"], hunter["y"])

        apply_hunter_darkness(self.screen, hunter["x"], hunter["y"])
        self.draw_hunter_noise(now)

        draw_hud(
            self.screen,
            self.font,
            self.small_font,
            role=self.role,
            time_left=float(self.state.get("time_left", GAME_DURATION)),
            winner=self.state.get("winner"),
            connected=connected,
            waiting_for_players=bool(self.state.get("waiting_for_players", True)),
            name=self.name,
        )

    def render_goat(self, now: float, connected: bool, input_state: dict[str, Any]) -> None:
        hunter = self.state["hunter"]
        goat = self.state["goat"]

        draw_map_base(self.screen, show_grid=True)
        draw_obstacles(self.screen)
        draw_traps(self.screen)
        draw_hunter(self.screen, hunter["x"], hunter["y"])
        draw_goat(self.screen, goat["x"], goat["y"])

        draw_hud(
            self.screen,
            self.font,
            self.small_font,
            role=self.role,
            time_left=float(self.state.get("time_left", GAME_DURATION)),
            winner=self.state.get("winner"),
            connected=connected,
            waiting_for_players=bool(self.state.get("waiting_for_players", True)),
            name=self.name,
        )

    def draw_hunter_noise(self, now: float) -> None:
        if not self.visible_noises:
            return

        still_active: list[dict[str, Any]] = []
        for noise in self.visible_noises:
            age = now - noise["received_at"]
            if age > NOISE_DISPLAY_SECONDS:
                continue
            draw_noise_signal(self.screen, noise["x"], noise["y"], age / NOISE_DISPLAY_SECONDS)
            still_active.append(noise)
        self.visible_noises = still_active


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Blind Goat Hunt Pygame client")
    parser.add_argument(
        "--role",
        choices=sorted(VALID_ROLES),
        help="Player role. Omit both --role and --server to open the setup menu.",
    )
    parser.add_argument("--server", help="Server IP/host. Omit to open the setup menu.")
    parser.add_argument("--port", default=5000, type=int, help="Server UDP port")
    parser.add_argument("--name", default="", help="Player name (shown in HUD)")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.role and args.server:
        # CLI mode — skip the menu, keep the legacy launch flow working.
        name = args.name or "Player"
        server = args.server
        port = args.port
        role = args.role
    else:
        # No role/server on the command line → show the setup menu.
        from menu import run_menu

        result = run_menu(
            default_name=args.name,
            default_server=args.server or "127.0.0.1",
            default_port=args.port,
        )
        if result is None:
            return
        name, server, port, role = result

    GameClient(role, server, port, name=name).run()


if __name__ == "__main__":
    main()
