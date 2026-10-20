"""Composable environmental hazards for standalone and combined campaign missions."""
import random

import pygame
from src.entities.reference_art import effect_frame


class DisasterSystem:
    def __init__(self, types, map_size, config=None):
        self.types = set(types)
        self.has_flood = bool(self.types & {"flood", "flash_flood", "severe_flood"})
        self.has_tsunami = "tsunami" in self.types
        self.map_w, self.map_h = map_size
        self.config = config or {}
        self.time = 0.0
        self.quake_timer = 0.75
        self.quake_warning = 0.0
        self.quake_active = 0.0
        self.damage_cooldown = {}
        self.rock_timer = 3.0
        self.rocks = []
        self.lahar_timer = float(self.config.get("lahar_interval", 11.0))
        self.lahars = []
        self.gas_timer = float(self.config.get("gas_interval", 9.0))
        self.gas_clouds = []
        self.slide_timer = float(self.config.get("landslide_interval", 6.0))
        self.slides = []
        self.flash_timer = float(self.config.get("flash_fire_interval", 6.5))
        self.flash_zones = []
        self.rng = random.Random(self.config.get("seed", 1))

    def update(self, dt, player, danger, safe_zones, events, quake_safe_zones=None,
               protective_mask=False):
        self.time += dt
        # Flood water climbs gradually; warnings are visible before it reaches the route.
        flood_active = (self.has_flood and
                        self.time >= float(self.config.get("flood_start_seconds", 0.0)))
        if flood_active or self.has_tsunami:
            line = self.waterline()
            sheltered = any(zone.colliderect(player.rect) for zone in safe_zones)
            if player.rect.centery >= line and not sheltered:
                self._damage("water", dt, player, events, 18, 1.35)

        if "earthquake" in self.types:
            self.quake_timer -= dt
            if self.quake_timer <= 0 and self.quake_warning <= 0 and self.quake_active <= 0:
                self.quake_warning = float(self.config.get("quake_warning_seconds", 4.0))
                self.quake_timer = max(8.0, 18.0 - danger * 0.055)
            elif self.quake_warning > 0:
                self.quake_warning -= dt
                if self.quake_warning <= 0:
                    self.quake_active = 2.4
            elif self.quake_active > 0:
                self.quake_active -= dt
                cover = safe_zones if quake_safe_zones is None else quake_safe_zones
                covered = any(z.colliderect(player.rect) for z in cover)
                if not covered:
                    self._damage("quake", dt, player, events, 16, 0.85)

        volcano_active = ("volcano" in self.types and
                          self.time >= float(self.config.get("volcano_start_seconds", 0.0)))
        if volcano_active:
            self.rock_timer -= dt
            if self.rock_timer <= 0:
                self.rock_timer = max(1.0, 3.3 - danger / 65)
                x = self.rng.randint(24, self.map_w - 24)
                y = self.rng.randint(24, self.map_h - 24)
                self.rocks.append({"rect": pygame.Rect(x - 12, y - 12, 24, 24), "warning": 1.25, "life": 2.4})
            for rock in self.rocks[:]:
                rock["warning"] -= dt
                rock["life"] -= dt
                if rock["warning"] <= 0 and rock["life"] > 1.0:
                    if rock["rect"].colliderect(player.rect):
                        self._damage("ashfall", dt, player, events, 12, 1.0)
                if rock["life"] <= 0:
                    self.rocks.remove(rock)

            self.lahar_timer -= dt
            if self.lahar_timer <= 0:
                self.lahar_timer = max(7.0, float(self.config.get("lahar_interval", 11.0)) - danger * 0.025)
                y = self.rng.randint(38, max(39, min(145, self.map_h - 70)))
                self.lahars.append({"y": float(y), "warning": 2.2, "life": 7.5})
            for lahar in self.lahars[:]:
                lahar["warning"] -= dt
                if lahar["warning"] <= 0:
                    lahar["y"] += dt * 55
                    flow = pygame.Rect(0, round(lahar["y"]), self.map_w, 34)
                    sheltered = any(zone.colliderect(player.rect) for zone in safe_zones)
                    if flow.colliderect(player.rect) and not sheltered:
                        self._damage("lahar", dt, player, events, 18, 0.8)
                lahar["life"] -= dt
                if lahar["life"] <= 0 or lahar["y"] > self.map_h:
                    self.lahars.remove(lahar)

            self.gas_timer -= dt
            if self.gas_timer <= 0:
                self.gas_timer = max(7.0, float(self.config.get("gas_interval", 9.0)) - danger * 0.02)
                rect = pygame.Rect(self.rng.randint(55, max(56, self.map_w - 95)),
                                   self.rng.randint(40, max(41, self.map_h - 100)), 72, 60)
                if not any(zone.colliderect(rect) for zone in safe_zones):
                    self.gas_clouds.append({"rect": rect, "warning": 2.0, "life": 6.5})
            for cloud in self.gas_clouds[:]:
                cloud["warning"] -= dt
                cloud["life"] -= dt
                if (cloud["warning"] <= 0 and cloud["rect"].colliderect(player.rect)
                        and not protective_mask):
                    self._damage("volcanic_gas", dt, player, events, 8, 1.0)
                if cloud["life"] <= 0:
                    self.gas_clouds.remove(cloud)

        # Landslide debris follows a clearly telegraphed downhill corridor.
        # The warning gives the player time to move out of its flow path.
        landslide_active = ("landslide" in self.types and
                            self.time >= float(self.config.get("landslide_start_seconds", 0.0)))
        if landslide_active:
            self.slide_timer -= dt
            if self.slide_timer <= 0:
                self.slide_timer = max(3.4, float(self.config.get("landslide_interval", 6.0)))
                lane_x = self.rng.choice((175, 270, 365, 460))
                self.slides.append({"x": lane_x, "y": -40.0, "warning": 1.4, "life": 6.0})
            for slide in self.slides[:]:
                slide["warning"] -= dt
                if slide["warning"] <= 0:
                    slide["y"] += dt * 112
                    hazard_rect = pygame.Rect(round(slide["x"] - 11), round(slide["y"]), 22, 48)
                    if hazard_rect.colliderect(player.rect):
                        self._damage("landslide", dt, player, events, 15, 1.0)
                slide["life"] -= dt
                if slide["life"] <= 0 or slide["y"] > self.map_h + 40:
                    self.slides.remove(slide)

        if "wildfire" in self.types:
            speed = float(self.config.get("wildfire_speed", 14)) * (1 + danger / 180)
            front = min(self.map_w + 40, self.time * speed)
            if player.rect.left <= front and player.rect.right >= front - 26:
                self._damage("wildfire", dt, player, events, 14, 0.75)

        if "flash_fire" in self.types:
            self.flash_timer -= dt
            if self.flash_timer <= 0:
                self.flash_timer = max(4.0, float(self.config.get("flash_fire_interval", 6.5)))
                x = self.rng.randint(64, max(65, self.map_w - 64))
                y = self.rng.randint(64, max(65, self.map_h - 64))
                self.flash_zones.append({"rect": pygame.Rect(x - 24, y - 24, 48, 48),
                                         "warning": 1.5, "life": 3.5})
            for zone in self.flash_zones[:]:
                zone["warning"] -= dt
                zone["life"] -= dt
                sheltered = any(area.colliderect(player.rect) for area in safe_zones)
                if zone["warning"] <= 0 and zone["rect"].colliderect(player.rect) and not sheltered:
                    self._damage("flash_fire", dt, player, events, 12, 0.9)
                if zone["life"] <= 0:
                    self.flash_zones.remove(zone)

    def _damage(self, source, dt, player, events, amount, interval):
        self.damage_cooldown.setdefault(source, 0.0)
        self.damage_cooldown[source] -= dt
        if self.damage_cooldown[source] <= 0:
            if player.take_damage(amount):
                events.emit("player_damaged", amount=amount, source=source)
            self.damage_cooldown[source] = interval

    def waterline(self):
        lines = []
        if self.has_flood and self.time >= float(self.config.get("flood_start_seconds", 0.0)):
            start = float(self.config.get("flood_start_seconds", 0.0))
            elapsed = max(0.0, self.time - start - 5.0)
            default_rate = 2.2 if "severe_flood" in self.types else 1.65 if "flash_flood" in self.types else 1.2
            rate = float(self.config.get("flood_rate", default_rate))
            default_escalation = 18.0 if "severe_flood" in self.types else 0.0
            escalation = float(self.config.get("flood_escalation_seconds", default_escalation))
            if escalation > 0:
                initial_rate = float(self.config.get("flood_rate_initial", 1.2))
                rise = min(elapsed, escalation) * initial_rate
                rise += max(0.0, elapsed - escalation) * rate
            else:
                rise = elapsed * rate
            lines.append(int(self.map_h + 10 - rise))
        if self.has_tsunami:
            delay = float(self.config.get("tsunami_warning_seconds", 38))
            surge = float(self.config.get("tsunami_surge_seconds", 16))
            if self.time >= delay:
                p = min(1.0, (self.time - delay) / surge)
                lines.append(int(self.map_h + 12 - (self.map_h + 30) * p))
        return min(lines) if lines else self.map_h + 1

    def in_unsafe_water(self, rect, safe_zones):
        if not (self.has_flood or self.has_tsunami):
            return False
        return rect.centery >= self.waterline() and not any(z.colliderect(rect) for z in safe_zones)

    @property
    def camera_shake(self):
        return self.quake_active > 0

    def current_alert(self):
        """Compact, accurate instruction for the active hazard state."""
        if self.quake_warning > 0:
            return "QUAKE: DROP, COVER, HOLD", (255, 226, 142)
        if self.quake_active > 0:
            return "SHAKING: HOLD COVER", (255, 157, 132)
        if self.has_tsunami:
            delay = float(self.config.get("tsunami_warning_seconds", 38))
            surge = float(self.config.get("tsunami_surge_seconds", 16))
            if self.time < delay + surge:
                return "TSUNAMI: MOVE INLAND", (255, 219, 119)
        if self.has_flood and self.time > 5 and self.waterline() < self.map_h - 24:
            escalation = float(self.config.get("flood_escalation_seconds", 0.0))
            flood_start = float(self.config.get("flood_start_seconds", 0.0))
            if escalation and self.time >= flood_start + 5 + escalation:
                return "FLOOD ESCALATING: MOVE TO HIGH GROUND", (154, 220, 255)
            if "severe_flood" in self.types:
                return "SEVERE FLOOD: MOVE TO HIGH GROUND", (154, 220, 255)
            return "FLASH FLOOD: SEEK HIGH GROUND", (154, 220, 255)
        if ("wildfire" in self.types or "flash_fire" in self.types) and self.time > 5:
            return "FIRE: EVACUATE EARLY", (255, 188, 126)
        if ("landslide" in self.types and
                self.time >= float(self.config.get("landslide_start_seconds", 0.0))):
            return "LANDSLIDE: CLEAR THE WARNED SLOPE", (255, 185, 115)
        if any(lahar["warning"] > 0 for lahar in self.lahars):
            return "LAHAR WARNING: MOVE OUT OF THE VALLEY", (255, 190, 123)
        if any(cloud["warning"] <= 0 for cloud in self.gas_clouds):
            return "VOLCANIC GAS: USE A MASK, MOVE AWAY", (202, 226, 158)
        if ("volcano" in self.types and
                self.time >= float(self.config.get("volcano_start_seconds", 0.0))):
            return "VOLCANO: AVOID VALLEYS, PROTECT BREATHING", (255, 192, 123)
        return "", (255, 255, 255)

    def draw_world(self, surface, camera):
        if ((self.has_flood and self.time >= float(self.config.get("flood_start_seconds", 0.0)))
                or self.has_tsunami):
            line = self.waterline()
            rect = pygame.Rect(0, line, self.map_w, self.map_h - line)
            if rect.h > 0:
                pygame.draw.rect(surface, (35, 105, 190), camera.apply(rect))
                rr = camera.apply(pygame.Rect(0, line, self.map_w, 3))
                pygame.draw.rect(surface, (130, 205, 245), rr)
                splash = effect_frame("water_splash", (27, 17), self.time)
                if splash:
                    for wx in range(42, self.map_w, 112):
                        point = camera.apply(pygame.Rect(wx, line - 5, 1, 1)).center
                        surface.blit(splash, splash.get_rect(center=point))

        if "wildfire" in self.types:
            front = min(self.map_w + 40, int(self.time * float(self.config.get("wildfire_speed", 14))))
            rect = camera.apply(pygame.Rect(front - 26, 0, 26, self.map_h))
            pygame.draw.rect(surface, (190, 50, 18), rect)
            flame = effect_frame("fire", (31, 36), self.time)
            if flame:
                for y in range(rect.y, rect.bottom, 32):
                    surface.blit(flame, flame.get_rect(center=(rect.centerx, y + 15)))

        for zone in self.flash_zones:
            rect = camera.apply(zone["rect"])
            if zone["warning"] > 0:
                if int(zone["warning"] * 6) % 2:
                    pygame.draw.ellipse(surface, (255, 218, 133), rect.inflate(10, 10), 2)
                pygame.draw.ellipse(surface, (241, 147, 88), rect, 1)
            else:
                flame = effect_frame("fire", (max(32, rect.w + 14),
                                               max(32, rect.h + 10)), self.time)
                if flame:
                    surface.blit(flame, flame.get_rect(center=rect.center))

        for slide in self.slides:
            x = int(slide["x"])
            if slide["warning"] > 0:
                warn = pygame.Rect(x - 16, 0, 32, self.map_h)
                pygame.draw.rect(surface, (245, 185, 74), camera.apply(warn), 1)
                if int(slide["warning"] * 5) % 2:
                    mark = camera.apply(pygame.Rect(x - 1, 0, 2, self.map_h))
                    pygame.draw.line(surface, (255, 215, 110), mark.topleft, mark.bottomleft, 2)
            else:
                rect = camera.apply(pygame.Rect(x - 11, int(slide["y"]), 22, 48))
                dust = effect_frame("dust", (max(24, rect.w + 8),
                                              max(30, rect.h)), self.time)
                if dust:
                    surface.blit(dust, dust.get_rect(center=rect.center))

        for rock in self.rocks:
            rect = camera.apply(rock["rect"])
            effect = "explosion" if rock["warning"] > 0 else "dust"
            art = effect_frame(effect, (max(20, rect.w + 10), max(20, rect.h + 10)), self.time)
            if art:
                surface.blit(art, art.get_rect(center=rect.center))

        for lahar in self.lahars:
            rect = camera.apply(pygame.Rect(0, round(lahar["y"]), self.map_w, 34))
            if lahar["warning"] > 0:
                pygame.draw.rect(surface, (237, 195, 103), rect, 1)
                if int(lahar["warning"] * 5) % 2:
                    pygame.draw.line(surface, (255, 224, 147), rect.midleft, rect.midright, 2)
            else:
                pygame.draw.rect(surface, (113, 68, 48), rect)
                pygame.draw.line(surface, (173, 112, 69), rect.midleft, rect.midright, 2)

        for cloud in self.gas_clouds:
            rect = camera.apply(cloud["rect"])
            color = (223, 226, 153) if cloud["warning"] > 0 else (165, 190, 125)
            pygame.draw.ellipse(surface, color, rect, 1 if cloud["warning"] > 0 else 2)
            for dx, dy, radius in ((12, 30, 8), (33, 18, 11), (52, 35, 9)):
                pygame.draw.circle(surface, color, (rect.x + dx, rect.y + dy), radius, 1)

    def draw_overlay(self, surface):
        if "volcano" in self.types or "landslide" in self.types:
            haze = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            haze.fill((115, 85, 65, 34))
            surface.blit(haze, (0, 0))
        # Hazard instructions live in the reserved HUD rail, not over the playfield.
