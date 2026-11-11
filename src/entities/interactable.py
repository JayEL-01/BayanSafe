"""Interactive environmental objects and points of interest (POIs).

Allows players to inspect signs, terminals, broken machinery, supply lockers,
and environmental details with classic Pokémon-style [E] EXAMINE prompts.
"""
import math
import pygame
from src.ui import theme


class Interactable:
    def __init__(self, data):
        self.id = data["id"]
        self.name = data["name"]
        rect_data = data["rect"]
        self.rect = pygame.Rect(*rect_data)
        self.lines = [str(l) for l in data.get("lines", [data.get("description", "...")])]
        self.prompt = data.get("prompt", "EXAMINE")
        self.icon = data.get("icon", "book")
        self.color = tuple(data.get("color", theme.BRASS))
        self.active = data.get("active", True)
        self.examined = False
        self.interact_range = data.get("range", 26)
        self.one_time = data.get("one_time", False)
        self.reward_item = data.get("reward_item")
        self.event_on_inspect = data.get("event")

    def is_near(self, player_rect):
        if not self.active:
            return False
        cx, cy = self.rect.center
        px, py = player_rect.center
        dist_sq = (cx - px) ** 2 + (cy - py) ** 2
        return dist_sq <= (self.interact_range ** 2)

    def inspect(self):
        self.examined = True
        if self.one_time:
            self.active = False
        return self.lines

    def draw(self, surface, camera, is_objective=False):
        if not self.active:
            return

        screen_rect = camera.apply(self.rect)
        if not screen_rect.colliderect(camera.viewport):
            return

        # Visual representation: Handcrafted wooden/brass plaque, marker or terminal
        pulse = (math.sin(pygame.time.get_ticks() / 250) + 1) / 2

        # Draw base object marker
        pygame.draw.rect(surface, theme.SHADOW, screen_rect.move(0, 1))
        bg_col = theme.mix(theme.WOOD_DARK, self.color, 0.25)
        pygame.draw.rect(surface, bg_col, screen_rect, border_radius=2)
        border_col = theme.BRASS_LIGHT if is_objective else theme.WOOD_BORDER
        pygame.draw.rect(surface, border_col, screen_rect, 1, border_radius=2)

        # Draw mini icon in center
        center = screen_rect.center
        theme.draw_icon(surface, self.icon, (center[0] - 4, center[1] - 4), self.color)

        # Objective highlight glow
        if is_objective:
            glow_r = int(screen_rect.width // 2 + 3 + pulse * 2)
            pygame.draw.circle(surface, (*theme.HONEY, 120), center, glow_r, 1)

    def draw_prompt(self, surface, camera):
        """Draw Pokémon-style animated floating [E] prompt pill above object."""
        if not self.active:
            return

        screen_rect = camera.apply(self.rect)
        t = pygame.time.get_ticks() / 1000
        bob = int(round(math.sin(t * 5.0) * 2.0))

        font = theme.get_font("tiny")
        tip_text = f"E: {self.prompt.upper()}"
        text_w, text_h = font.size(tip_text)

        pill_w = text_w + 10
        pill_h = text_h + 4
        pill_x = screen_rect.centerx - pill_w // 2
        pill_y = screen_rect.top - pill_h - 4 + bob

        # Drop shadow & pill background
        pill_rect = pygame.Rect(pill_x, pill_y, pill_w, pill_h)
        pygame.draw.rect(surface, theme.SHADOW, pill_rect.move(0, 1), border_radius=3)
        pygame.draw.rect(surface, theme.DARK_OAK, pill_rect, border_radius=3)
        pygame.draw.rect(surface, theme.BRASS, pill_rect, 1, border_radius=3)

        # Little downward triangle pointer
        tri_x = screen_rect.centerx
        tri_y = pill_rect.bottom
        pygame.draw.polygon(surface, theme.DARK_OAK, [
            (tri_x - 3, tri_y), (tri_x + 3, tri_y), (tri_x, tri_y + 3)
        ])
        pygame.draw.polygon(surface, theme.BRASS, [
            (tri_x - 3, tri_y), (tri_x + 3, tri_y), (tri_x, tri_y + 3)
        ], 1)

        theme.draw_text(surface, tip_text, (pill_rect.centerx, pill_rect.centery),
                        font, theme.CREAM, anchor="center", shadow=False)
