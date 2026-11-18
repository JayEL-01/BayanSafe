import pygame

from src.core import settings
from src.states.base_state import BaseState
from src.ui import code_art, theme


class LoadingScreen(BaseState):
    """Animated, readable transition between campaign scenes."""

    def __init__(self, game, build_next, message="PREPARING YOUR MISSION", duration=0.65,
                 journey_map=False):
        super().__init__(game)
        self.build_next = build_next
        self.message = message
        self.duration = duration
        self.elapsed = 0.0
        self.journey_map = journey_map
        self.map_image = None
        shade_color = (*theme.NIGHT, 155) if journey_map else (0, 0, 0, 0)
        self.shade = pygame.Surface((settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT), pygame.SRCALPHA)
        self.shade.fill(shade_color)
        if journey_map:
            image = code_art.layer("mount_talon_island_map.png")
            if image is not None:
                self.map_image = pygame.transform.smoothscale(
                    image, (settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT)
                )

    def update(self, dt):
        self.elapsed += dt
        if self.elapsed >= self.duration:
            self.game.state_manager.change(self.build_next())

    def draw(self, surface):
        if self.map_image:
            surface.blit(self.map_image, (0, 0))
            surface.blit(self.shade, (0, 0))
        else:
            theme.draw_background(surface)
            # Subtle moving horizon grain gives short non-map transitions life too.
            drift = int(self.elapsed * 18) % 320
            horizon_color = theme.WOOD_GRAIN
            for i in range(7):
                x = (i * 57 - drift) % 360 - 20
                pygame.draw.line(surface, horizon_color, (x, 0), (x - 42, 180), 1)
            top_bar = theme.DARK_OAK
            pygame.draw.rect(surface, top_bar, (0, 0, settings.INTERNAL_WIDTH, 72))

        progress = min(1.0, self.elapsed / max(self.duration, 0.01))
        theme.draw_text(surface, "BAYANSAFE", (160, 28), "heading", theme.HONEY,
                        anchor="center")

        # A small responder walks the dotted route while the next scene loads.
        # This keeps the transition visually clear without introducing asset dependencies.
        panel = pygame.Rect(38, 48, 244, 100)
        theme.draw_panel(surface, panel, accent=theme.HONEY, alpha=238)
        route_y = 78
        route_left, route_right = 67, 253
        dot_color = theme.mix(theme.SAGE, theme.SKY, 0.3)  # ~ (115, 151, 125)
        for i in range(13):
            x = route_left + i * 15
            if x <= route_right:
                pygame.draw.circle(surface, dot_color, (x, route_y), 1)

        # The marker eases from the start to the next stop, then stays there
        # for any remaining loading time. Its bob and stepping legs keep it animated.
        marker_x = round(route_left + (route_right - route_left) * progress)
        phase = self.elapsed * 13.0
        bob = round(abs(pygame.math.Vector2(0, 1).rotate(phase * 18).y) * 1.5)
        head_y = route_y - 10 - bob
        pygame.draw.circle(surface, theme.HONEY, (marker_x, route_y), 7, 1)
        pygame.draw.circle(surface, theme.CREAM, (marker_x, head_y), 2)
        pygame.draw.line(surface, theme.SAGE, (marker_x, head_y + 3), (marker_x, route_y - 2), 2)
        step = round(pygame.math.Vector2(0, 1).rotate(phase * 35).x * 2)
        pygame.draw.line(surface, theme.CREAM, (marker_x, route_y - 2), (marker_x - 3, route_y + 1 + step), 1)
        pygame.draw.line(surface, theme.CREAM, (marker_x, route_y - 2), (marker_x + 3, route_y + 1 - step), 1)

        theme.draw_text(surface, self.message, (160, 101), "small", theme.CREAM,
                        anchor="center")
        bar = pygame.Rect(69, 119, 182, 7)
        bar_bg = theme.WOOD_DARK
        pygame.draw.rect(surface, bar_bg, bar, border_radius=3)
        pygame.draw.rect(surface, theme.WOOD_BORDER, bar, 1, border_radius=3)
        fill_w = round((bar.w - 2) * progress)
        if fill_w > 0:
            pygame.draw.rect(surface, theme.HONEY, (bar.x + 1, bar.y + 1, fill_w, bar.h - 2),
                             border_radius=2)
            # A moving highlight makes progress visible even during quick transitions.
            shine_x = bar.x + min(fill_w, int((self.elapsed * 90) % max(fill_w, 1)))
            pygame.draw.line(surface, theme.CREAM, (shine_x, bar.y + 2),
                             (min(shine_x + 5, bar.x + fill_w), bar.bottom - 2), 1)
        pulse = (pygame.time.get_ticks() // 320) % 4
        theme.draw_text(surface, "PREPARING" + "." * pulse, (160, 137), "tiny",
                        theme.CREAM_DIM, anchor="center")
