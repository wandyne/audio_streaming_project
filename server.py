"""UDP game server for Blind Goat Hunt.

Run:
    python server.py --host 0.0.0.0 --port 5000

The server owns gameplay state: positions, timer, collision, win conditions,
and fake audio/noise events. Clients only send role input.
"""

from __future__ import annotations

import argparse
import math
import time
from dataclasses import dataclass
from typing import Any

from game_objects import distance, move_with_obstacles
from network import create_udp_socket, recv_json, send_json
from settings import (
    CATCH_RADIUS,
    CLIENT_SEND_RATE,
    GAME_DURATION,
    GOAT_IDLE_NOISE_AFTER,
    GOAT_OBSTACLE_NOISE_COOLDOWN,
    GOAT_REQUIRES_NOISE_TO_MOVE,
    GOAT_SPEED,
    GOAT_START,
    HUNTER_SCAN_INTERVAL,
    HUNTER_SPEED,
    HUNTER_START,
    INPUT_STALE_SECONDS,
    NETWORK_TIMEOUT_SECONDS,
    OBSTACLES,
    PLAYER_RADIUS,
    SERVER_TICK_RATE,
    TRAP_NOISE_COOLDOWN,
    TRAPS,
)


VALID_ROLES = {"hunter", "goat"}


@dataclass
class PlayerInput:
    dx: float = 0.0
    dy: float = 0.0
    moving: bool = False
    making_noise: bool = False
    last_seen: float = 0.0


class GameServer:
    def __init__(self, host: str, port: int) -> None:
        self.sock = create_udp_socket(host, port)
        self.host = host
        self.port = port
        self.clients: dict[str, tuple[str, int]] = {}
        self.inputs = {"hunter": PlayerInput(), "goat": PlayerInput()}
        self.last_broadcast = 0.0
        self.noise_id = 0
        self.noise_event: dict[str, Any] | None = None
        self.reset_game()

    def reset_game(self) -> None:
        self.hunter = {"x": float(HUNTER_START[0]), "y": float(HUNTER_START[1])}
        self.goat = {"x": float(GOAT_START[0]), "y": float(GOAT_START[1])}
        self.time_left = GAME_DURATION
        self.winner: str | None = None
        self.started_at: float | None = None
        self.last_tick = time.monotonic()

        now = time.monotonic()
        self.goat_idle_started_at: float | None = now
        self.goat_idle_noise_fired = False
        self.last_goat_obstacle_noise_at = -999.0
        self.last_trap_noise_at: dict[int, float] = {}

        self.hunter_standing_started_at: float | None = now
        self.last_hunter_scan_at: float | None = None

        self.noise_event = None

    def run(self) -> None:
        print(f"Blind Goat Hunt server listening on {self.host}:{self.port}")
        tick_seconds = 1.0 / SERVER_TICK_RATE

        try:
            while True:
                now = time.monotonic()
                dt = min(0.05, now - self.last_tick)
                self.last_tick = now

                self.receive_packets(now)
                self.update(dt, now)

                if now - self.last_broadcast >= 1.0 / CLIENT_SEND_RATE:
                    self.broadcast_state(now)
                    self.last_broadcast = now

                sleep_for = max(0.001, tick_seconds - (time.monotonic() - now))
                time.sleep(sleep_for)
        except KeyboardInterrupt:
            print("\nServer stopped.")

    def receive_packets(self, now: float) -> None:
        for message, address in recv_json(self.sock):
            role = message.get("role")
            if role not in VALID_ROLES:
                continue

            self.clients[role] = address
            player_input = self.inputs[role]
            player_input.dx = safe_axis(message.get("dx", 0))
            player_input.dy = safe_axis(message.get("dy", 0))
            player_input.moving = bool(message.get("moving", False))
            player_input.making_noise = bool(message.get("making_noise", False))
            player_input.last_seen = now

            if message.get("reset"):
                self.reset_game()

            # Reply immediately so a newly opened client does not wait for the
            # next broadcast interval to draw something useful.
            send_json(self.sock, self.build_state(now), address)

    def update(self, dt: float, now: float) -> None:
        self.drop_disconnected_clients(now)

        if not self.has_both_players():
            self.update_lobby_movement(dt, now)
            self.started_at = None
            return

        if self.started_at is None:
            self.started_at = now
            self.goat_idle_started_at = now
            self.goat_idle_noise_fired = False
            self.hunter_standing_started_at = now
            self.last_hunter_scan_at = None

        if self.winner is not None:
            return

        self.time_left = max(0.0, self.time_left - dt)
        if self.time_left <= 0:
            self.time_left = 0
            self.winner = "goat"
            return

        hunter_input = self.fresh_input("hunter", now)
        goat_input = self.fresh_input("goat", now)

        self.update_hunter(hunter_input, dt, now)
        self.update_goat(goat_input, dt, now)

        if distance((self.hunter["x"], self.hunter["y"]), (self.goat["x"], self.goat["y"])) <= CATCH_RADIUS:
            self.winner = "hunter"

    def update_lobby_movement(self, dt: float, now: float) -> None:
        """Allow quick movement testing before both clients have joined."""
        if "hunter" in self.clients:
            self.update_hunter(self.fresh_input("hunter", now), dt, now)
        if "goat" in self.clients:
            self.update_goat(self.fresh_input("goat", now), dt, now)

    def update_hunter(self, player_input: PlayerInput, dt: float, now: float) -> None:
        moving = has_direction(player_input)

        if moving:
            self.hunter["x"], self.hunter["y"], _ = move_with_obstacles(
                self.hunter["x"],
                self.hunter["y"],
                player_input.dx,
                player_input.dy,
                HUNTER_SPEED,
                dt,
                can_pass_obstacles=True,
            )
            self.hunter_standing_started_at = None
            self.last_hunter_scan_at = None
            return

        if self.hunter_standing_started_at is None:
            self.hunter_standing_started_at = now
            self.last_hunter_scan_at = None
            return

        standing_for = now - self.hunter_standing_started_at
        ready_for_first_scan = self.last_hunter_scan_at is None and standing_for >= HUNTER_SCAN_INTERVAL
        ready_for_next_scan = (
            self.last_hunter_scan_at is not None and now - self.last_hunter_scan_at >= HUNTER_SCAN_INTERVAL
        )
        if ready_for_first_scan or ready_for_next_scan:
            self.emit_noise("hunter_standing_scan", self.goat["x"], self.goat["y"], now)
            self.last_hunter_scan_at = now

    def update_goat(self, player_input: PlayerInput, dt: float, now: float) -> None:
        trying_to_move = has_direction(player_input)

        if not trying_to_move:
            if self.goat_idle_started_at is None:
                self.goat_idle_started_at = now
                self.goat_idle_noise_fired = False
            elif not self.goat_idle_noise_fired and now - self.goat_idle_started_at >= GOAT_IDLE_NOISE_AFTER:
                self.emit_noise("goat_stopped_too_long", self.goat["x"], self.goat["y"], now)
                self.goat_idle_noise_fired = True
        else:
            self.goat_idle_started_at = None
            self.goat_idle_noise_fired = False

        # Current DSP placeholder: goat movement is gated by making_noise.
        # Team audio can replace client SPACE input with mic_volume > threshold.
        can_move = trying_to_move and (player_input.making_noise or not GOAT_REQUIRES_NOISE_TO_MOVE)
        if not can_move:
            return

        self.goat["x"], self.goat["y"], blocked = move_with_obstacles(
            self.goat["x"],
            self.goat["y"],
            player_input.dx,
            player_input.dy,
            GOAT_SPEED,
            dt,
            can_pass_obstacles=False,
        )

        if blocked and now - self.last_goat_obstacle_noise_at >= GOAT_OBSTACLE_NOISE_COOLDOWN:
            self.emit_noise("goat_hit_obstacle", self.goat["x"], self.goat["y"], now)
            self.last_goat_obstacle_noise_at = now

        self.check_trap_noise(now)

    def check_trap_noise(self, now: float) -> None:
        for index, trap in enumerate(TRAPS):
            trap_radius = float(trap.get("radius", 12)) + PLAYER_RADIUS
            trap_position = (float(trap["x"]), float(trap["y"]))
            goat_position = (self.goat["x"], self.goat["y"])
            if distance(goat_position, trap_position) > trap_radius:
                continue

            last_noise_at = self.last_trap_noise_at.get(index, -999.0)
            if now - last_noise_at >= TRAP_NOISE_COOLDOWN:
                self.emit_noise("goat_triggered_trap", trap_position[0], trap_position[1], now)
                self.last_trap_noise_at[index] = now
            break

    def fresh_input(self, role: str, now: float) -> PlayerInput:
        player_input = self.inputs[role]
        if now - player_input.last_seen <= INPUT_STALE_SECONDS:
            return player_input
        return PlayerInput(last_seen=player_input.last_seen)

    def emit_noise(self, reason: str, x: float, y: float, now: float) -> None:
        self.noise_id += 1
        self.noise_event = {
            "active": True,
            "id": self.noise_id,
            "x": round(float(x), 2),
            "y": round(float(y), 2),
            "reason": reason,
            "timestamp": now,
        }
        print(f"noise_event #{self.noise_id}: {reason} at ({x:.1f}, {y:.1f})")

    def build_state(self, now: float) -> dict[str, Any]:
        connected_roles = {
            role: role in self.clients and now - self.inputs[role].last_seen <= NETWORK_TIMEOUT_SECONDS
            for role in VALID_ROLES
        }
        return {
            "type": "state",
            "hunter": {"x": round(self.hunter["x"], 2), "y": round(self.hunter["y"], 2)},
            "goat": {"x": round(self.goat["x"], 2), "y": round(self.goat["y"], 2)},
            "time_left": round(self.time_left, 2),
            "winner": self.winner,
            "noise_event": self.noise_event or {"active": False},
            "connected": connected_roles,
            "waiting_for_players": not self.has_both_players(),
            "obstacles": OBSTACLES,
            "traps": TRAPS,
            "server_time": now,
        }

    def broadcast_state(self, now: float) -> None:
        state = self.build_state(now)
        for address in set(self.clients.values()):
            send_json(self.sock, state, address)

    def has_both_players(self) -> bool:
        return "hunter" in self.clients and "goat" in self.clients

    def drop_disconnected_clients(self, now: float) -> None:
        for role in list(self.clients):
            if now - self.inputs[role].last_seen > NETWORK_TIMEOUT_SECONDS:
                print(f"{role} timed out")
                del self.clients[role]


def safe_axis(value: Any) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.0
    if math.isnan(number) or math.isinf(number):
        return 0.0
    return max(-1.0, min(1.0, number))


def has_direction(player_input: PlayerInput) -> bool:
    return abs(player_input.dx) > 0.01 or abs(player_input.dy) > 0.01


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Blind Goat Hunt UDP server")
    parser.add_argument("--host", default="0.0.0.0", help="Host/IP to bind")
    parser.add_argument("--port", default=5000, type=int, help="UDP port")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    GameServer(args.host, args.port).run()


if __name__ == "__main__":
    main()
