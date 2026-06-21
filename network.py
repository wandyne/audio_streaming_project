"""Small JSON-over-UDP helpers used by both server and client."""

from __future__ import annotations

import json
import socket
from typing import Any

from settings import PACKET_SIZE


def create_udp_socket(host: str | None = None, port: int | None = None) -> socket.socket:
    """Create a non-blocking UDP socket, optionally bound to host/port."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setblocking(False)
    if host is not None and port is not None:
        sock.bind((host, port))
    return sock


def send_json(sock: socket.socket, message: dict[str, Any], address: tuple[str, int]) -> None:
    """Send a JSON datagram. Invalid network states are ignored for demo safety."""
    try:
        payload = json.dumps(message, separators=(",", ":")).encode("utf-8")
        sock.sendto(payload, address)
    except OSError:
        # UDP has no connection state. A failed send should not crash the demo UI.
        pass


def recv_json(sock: socket.socket) -> list[tuple[dict[str, Any], tuple[str, int]]]:
    """Drain all currently available UDP packets from a non-blocking socket."""
    packets: list[tuple[dict[str, Any], tuple[str, int]]] = []
    while True:
        try:
            data, address = sock.recvfrom(PACKET_SIZE)
        except BlockingIOError:
            break
        except OSError:
            break

        try:
            message = json.loads(data.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            continue

        if isinstance(message, dict):
            packets.append((message, address))

    return packets
