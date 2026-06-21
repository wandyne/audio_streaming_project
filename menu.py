"""Pre-game setup menu for Blind Goat Hunt.

Shown by client.py when no --role / --server arguments are passed. Lets the
player type a name, the server IP, and the port, then pick a role to start the
game. Returns (name, server, port, role) or None if the user closes the window.
"""

from __future__ import annotations

import pygame

from settings import COLORS, WINDOW_HEIGHT, WINDOW_WIDTH


class TextField:
    """Click-to-focus text field. Tab cycles to the next field (handled outside)."""

    def __init__(
        self,
        rect: tuple[int, int, int, int],
        label: str,
        *,
        initial: str = "",
        max_len: int = 40,
        placeholder: str = "",
        digits_only: bool = False,
    ) -> None:
        self.rect = pygame.Rect(rect)
        self.label = label
        self.text = initial
        self.max_len = max_len
        self.placeholder = placeholder
        self.digits_only = digits_only
        self.focused = False

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.focused = self.rect.collidepoint(event.pos)
            return

        if not self.focused or event.type != pygame.KEYDOWN:
            return

        if event.key == pygame.K_BACKSPACE:
            self.text = self.text[:-1]
        elif event.key in (pygame.K_TAB, pygame.K_RETURN, pygame.K_KP_ENTER):
            # Handled by the outer loop (tab cycle / submit).
            return
        elif event.unicode and event.unicode.isprintable() and len(self.text) < self.max_len:
            if self.digits_only and not event.unicode.isdigit():
                return
            self.text += event.unicode

    def draw(self, surface: pygame.Surface, font: pygame.font.Font, small_font: pygame.font.Font) -> None:
        # Label above the field.
        label_surf = small_font.render(self.label, True, COLORS["muted_text"])
        surface.blit(label_surf, (self.rect.x, self.rect.y - 24))

        # Field box. Border colour highlights when focused.
        border = COLORS["hunter"] if self.focused else COLORS["border"]
        pygame.draw.rect(surface, COLORS["map_floor"], self.rect, border_radius=6)
        pygame.draw.rect(surface, border, self.rect, 2, border_radius=6)

        # Text or placeholder.
        if self.text:
            text_surf = font.render(self.text, True, COLORS["text"])
        else:
            text_surf = font.render(self.placeholder, True, COLORS["muted_text"])
        text_y = self.rect.y + (self.rect.height - text_surf.get_height()) // 2
        surface.blit(text_surf, (self.rect.x + 12, text_y))

        # Blinking cursor when focused.
        if self.focused and (pygame.time.get_ticks() // 500) % 2 == 0:
            measured = font.render(self.text, True, COLORS["text"]).get_width() if self.text else 0
            cursor_x = self.rect.x + 12 + measured
            top = self.rect.y + 10
            bottom = self.rect.y + self.rect.height - 10
            pygame.draw.line(surface, COLORS["text"], (cursor_x, top), (cursor_x, bottom), 2)


class Button:
    def __init__(self, rect: tuple[int, int, int, int], label: str, color: tuple[int, int, int]) -> None:
        self.rect = pygame.Rect(rect)
        self.label = label
        self.color = color
        self.hovered = False

    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                return True
        return False

    def draw(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        # Dim the fill until hover for a clear affordance.
        fill = self.color if self.hovered else tuple(int(c * 0.78) for c in self.color)
        pygame.draw.rect(surface, fill, self.rect, border_radius=10)
        pygame.draw.rect(surface, COLORS["text"], self.rect, 2, border_radius=10)
        label_surf = font.render(self.label, True, COLORS["background"])
        surface.blit(label_surf, label_surf.get_rect(center=self.rect.center))


def run_menu(
    default_name: str = "",
    default_server: str = "127.0.0.1",
    default_port: int = 5000,
) -> tuple[str, str, int, str] | None:
    """Run the setup menu loop. Returns (name, server, port, role) or None on quit."""
    pygame.init()
    pygame.display.set_caption("Blind Goat Hunt - Setup")
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    clock = pygame.time.Clock()

    title_font = pygame.font.SysFont(None, 60)
    field_font = pygame.font.SysFont(None, 32)
    button_font = pygame.font.SysFont(None, 34)
    small_font = pygame.font.SysFont(None, 22)

    cx = WINDOW_WIDTH // 2
    field_w = 420
    name_field = TextField(
        (cx - field_w // 2, 210, field_w, 44),
        "Your name",
        initial=default_name,
        max_len=20,
        placeholder="e.g. Latte",
    )
    server_field = TextField(
        (cx - field_w // 2, 300, field_w, 44),
        "Server IP",
        initial=default_server,
        max_len=40,
        placeholder="e.g. 192.168.1.23",
    )
    port_field = TextField(
        (cx - field_w // 2, 390, field_w, 44),
        "Port",
        initial=str(default_port),
        max_len=5,
        digits_only=True,
    )
    fields = [name_field, server_field, port_field]
    name_field.focused = True

    btn_w, btn_h, gap = 200, 58, 24
    btn_y = 480
    hunter_btn = Button(
        (cx - btn_w - gap // 2, btn_y, btn_w, btn_h),
        "Play as Hunter",
        COLORS["hunter"],
    )
    goat_btn = Button(
        (cx + gap // 2, btn_y, btn_w, btn_h),
        "Play as Goat",
        COLORS["goat"],
    )

    error_message = ""

    def validate_and_return(role: str) -> tuple[str, str, int, str] | str:
        name = name_field.text.strip()
        server = server_field.text.strip()
        port_str = port_field.text.strip()
        if not name:
            return "Please enter your name."
        if not server:
            return "Please enter the server IP."
        try:
            port_val = int(port_str)
        except ValueError:
            return "Port must be a number."
        if not (1 <= port_val <= 65535):
            return "Port must be between 1 and 65535."
        return name, server, port_val, role

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None

            # Tab cycles focus between fields.
            if event.type == pygame.KEYDOWN and event.key == pygame.K_TAB:
                current = next((i for i, f in enumerate(fields) if f.focused), -1)
                for f in fields:
                    f.focused = False
                fields[(current + 1) % len(fields)].focused = True
                continue

            for field in fields:
                field.handle_event(event)

            clicked_hunter = hunter_btn.handle_event(event)
            clicked_goat = goat_btn.handle_event(event)

            if clicked_hunter or clicked_goat:
                role = "hunter" if clicked_hunter else "goat"
                result = validate_and_return(role)
                if isinstance(result, tuple):
                    return result
                error_message = result

        screen.fill(COLORS["background"])

        title = title_font.render("Blind Goat Hunt", True, COLORS["text"])
        screen.blit(title, title.get_rect(center=(cx, 90)))
        subtitle = small_font.render(
            "Fill in your details, then choose a role to start.",
            True,
            COLORS["muted_text"],
        )
        screen.blit(subtitle, subtitle.get_rect(center=(cx, 140)))

        for field in fields:
            field.draw(screen, field_font, small_font)

        hunter_btn.draw(screen, button_font)
        goat_btn.draw(screen, button_font)

        if error_message:
            err = small_font.render(error_message, True, COLORS["danger"])
            screen.blit(err, err.get_rect(center=(cx, btn_y + btn_h + 28)))

        # Hint footer.
        hint = small_font.render(
            "Tab to switch fields  |  Esc/X to quit",
            True,
            COLORS["muted_text"],
        )
        screen.blit(hint, hint.get_rect(center=(cx, WINDOW_HEIGHT - 26)))

        pygame.display.flip()
        clock.tick(60)
