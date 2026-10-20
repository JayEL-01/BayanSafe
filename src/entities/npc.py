"""Animated pixel-art villagers with short, collision-aware walking routes."""
import math
import random
from collections import deque

import pygame
from src.entities.reference_art import character_sprite_for, npc_walk_sheet_for


SKIN_TONES = ((235, 190, 150), (211, 158, 118), (181, 125, 91), (244, 204, 162))
HAIR_TONES = ((55, 39, 34), (82, 53, 38), (46, 43, 40), (111, 73, 47))
PANTS_TONES = ((60, 74, 92), (77, 83, 62), (100, 64, 52), (67, 58, 77))


class NPC:
    WORLD_SPRITE_SIZE = (18, 27)

    def __init__(self, data):
        self.id = data["id"]
        self.name = data["name"]
        self.reference_sprite = character_sprite_for(self.name, data.get("id", ""))
        self.walk_sheet = npc_walk_sheet_for(self.name, data.get("id", ""))
        self.home = pygame.Vector2(data["pos"][0] + 6, data["pos"][1] + 6)
        self.pos = self.home.copy()
        self.rect = pygame.Rect(0, 0, 12, 12)
        self.rect.center = self.home
        self.color = tuple(data["color"])
        seed = sum((index + 1) * ord(char) for index, char in enumerate(self.id))
        self.rng = random.Random(seed)
        self.skin = self.rng.choice(SKIN_TONES)
        self.hair = self.rng.choice(HAIR_TONES)
        self.pants = self.rng.choice(PANTS_TONES)
        identity = f"{self.id} {self.name}".lower()
        if "tarsi" in identity or "leader" in identity:
            self.style = "responder"
        elif "kapitan" in identity or "captain" in identity:
            self.style = "captain"
        elif "mang" in identity:
            self.style = "elder_man"
        elif any(word in identity for word in ("lola", "nanay", "aling")):
            self.style = "elder_woman"
        elif "ate" in identity:
            self.style = "adult_woman"
        else:
            self.style = self.rng.choice(("farmer", "parent", "volunteer"))
        if self.style.startswith("elder"):
            self.hair = (174, 168, 151)
        self.dialogue = data["dialogue"]
        self.after_dialogue = data.get("after_dialogue", data["dialogue"])
        self.talked = False
        self.choice = data.get("choice")
        self.rescue_item = data.get("rescue_item")
        self.rescue_dialogue = data.get("rescue_dialogue", [])
        self.rescue_success_dialogue = data.get("rescue_success_dialogue", [])
        self.rescue_hint = data.get("rescue_hint", "Find the requested supply, then speak with me again.")
        self.needs_carry = bool(data.get("needs_carry", False))
        self.rescued = False
        self.following = False
        self.carried = False
        self.follow_map_size = None
        self.follow_repath = 0.0
        self.evacuating = False
        self.evacuated = False
        self.evacuation_path = []
        self.evacuation_goal = None
        self.evacuation_map_size = None
        self.evacuation_repath = 0.0
        self.path_collision = None
        self.time = self.rng.random() * 5
        self.walk_time = 0.0
        self.pause = self.rng.uniform(0.4, 1.8)
        self.target = self.pos.copy()
        self.facing = pygame.Vector2(0, 1)
        self.walk_speed = self.rng.uniform(7.0, 10.0)
        self.is_leader = any(word in self.name.lower() for word in ("kapitan", "captain", "leader"))

    def get_lines(self):
        return self.after_dialogue if self.talked else self.dialogue

    def is_near(self, player_rect, distance=14):
        return player_rect.inflate(distance * 2, distance * 2).colliderect(self.rect)

    def _pick_target(self, walls, collision=None):
        for _ in range(8):
            delta = pygame.Vector2(self.rng.uniform(-17, 17), self.rng.uniform(-13, 13))
            candidate = self.home + delta
            probe = self.rect.copy()
            probe.center = candidate
            if (not any(probe.colliderect(wall) for wall in walls)
                    and not (collision and collision.is_blocked(probe))):
                self.target = candidate
                return
        self.target = self.pos.copy()

    def evacuate(self, destination, walls, map_size, collision=None):
        """Walk to the stage's safe area using a tile path around obstacles."""
        self.evacuating = True
        self.following = False
        self.evacuated = False
        self.evacuation_goal = pygame.Rect(destination)
        self.evacuation_map_size = map_size
        self.path_collision = collision
        self.evacuation_repath = 0.0
        self.walk_speed = max(self.walk_speed, 46.0)
        self._plan_path(destination, walls, map_size, collision)

    def start_following(self, map_size, collision=None):
        self.following = True
        self.evacuating = False
        self.evacuated = False
        self.carried = False
        self.evacuation_goal = None
        self.evacuation_map_size = None
        self.evacuation_repath = 0.0
        self.follow_map_size = map_size
        self.path_collision = collision
        self.follow_repath = 0.0
        self.walk_speed = max(self.walk_speed, 70.0)

    def _plan_path(self, destination, walls, map_size, collision=None):
        collision = collision or self.path_collision
        if collision is not None:
            self.evacuation_path = collision.find_path(
                self.pos, destination, walls=walls, actor_size=self.rect.size
            )
            return bool(self.evacuation_path)
        cell = 8
        cols, rows = map_size[0] // cell, map_size[1] // cell
        start = (int(self.pos.x // cell), int(self.pos.y // cell))
        goal_point = pygame.Vector2(destination.center)
        goal = (int(goal_point.x // cell), int(goal_point.y // cell))
        blocked = set()
        for gy in range(rows):
            for gx in range(cols):
                probe = self.rect.copy()
                probe.center = (gx * cell + cell // 2, gy * cell + cell // 2)
                if any(probe.colliderect(wall) for wall in walls):
                    blocked.add((gx, gy))
        if start in blocked:
            blocked.discard(start)
        queue = deque([start])
        previous = {start: None}
        found = None
        directions = ((1, 0), (-1, 0), (0, 1), (0, -1))
        while queue:
            current = queue.popleft()
            goal_probe = self.rect.copy()
            goal_probe.center = (current[0] * cell + cell // 2,
                                 current[1] * cell + cell // 2)
            if goal_probe.colliderect(destination):
                found = current
                break
            for dx, dy in directions:
                nxt = (current[0] + dx, current[1] + dy)
                if (nxt in previous or nxt in blocked or nxt[0] <= 0 or nxt[1] <= 0
                        or nxt[0] >= cols - 1 or nxt[1] >= rows - 1):
                    continue
                previous[nxt] = current
                queue.append(nxt)
        if found is None:
            # Keep moving toward the refuge even if unusual geometry defeats
            # the grid route; collision handling in update will stop at walls.
            self.evacuation_path = [goal_point]
            return
        path = []
        while found is not None and found != start:
            path.append(pygame.Vector2(found[0] * cell + cell // 2,
                                       found[1] * cell + cell // 2))
            found = previous[found]
        self.evacuation_path = list(reversed(path))

    def update_following(self, player_rect, dt, walls, collision=None):
        collision = collision or self.path_collision
        if not self.following or self.carried:
            return
        self.follow_repath = max(0.0, self.follow_repath - dt)
        delta = pygame.Vector2(player_rect.center) - self.pos
        if delta.length_squared() <= 23 * 23:
            self.evacuation_path.clear()
        elif self.follow_repath <= 0:
            direction = delta.normalize()
            target = pygame.Vector2(player_rect.center) - direction * 20
            self._plan_path(pygame.Rect(round(target.x), round(target.y), 1, 1),
                            walls, self.follow_map_size, collision)
            self.follow_repath = 0.55

    def update(self, dt, walls, collision=None):
        collision = collision or self.path_collision
        self.time += dt
        if self.carried:
            self.walk_time = 0.0
            return
        if self.evacuating and self.evacuation_goal and self.evacuation_goal.colliderect(self.rect):
            self.evacuated = True
            self.evacuating = False
            self.evacuation_path.clear()
            self.walk_time = 0.0
            return
        if self.evacuating or self.following:
            while self.evacuation_path and self.pos.distance_squared_to(self.evacuation_path[0]) < 0.25:
                self.evacuation_path.pop(0)
            if not self.evacuation_path:
                if self.evacuating and not self.evacuated and self.evacuation_goal:
                    self.evacuation_repath = max(0.0, self.evacuation_repath - dt)
                    if self.evacuation_repath <= 0:
                        self._plan_path(self.evacuation_goal, walls, self.evacuation_map_size,
                                        collision or self.path_collision)
                        self.evacuation_repath = 0.5
                self.walk_time = 0.0
                return
            delta = self.evacuation_path[0] - self.pos
            self.facing = delta.normalize() if delta.length_squared() else self.facing
            step = self.facing * min(self.walk_speed * dt, delta.length())
            proposed = self.pos + step
            probe = self.rect.copy()
            probe.center = (round(proposed.x), round(proposed.y))
            if (any(probe.colliderect(wall) for wall in walls)
                    or ((collision or self.path_collision)
                        and (collision or self.path_collision).is_blocked(probe))):
                self.evacuation_path = []
                self.evacuation_repath = 0.25
                return
            self.pos = proposed
            self.rect.center = (round(self.pos.x), round(self.pos.y))
            self.walk_time += dt
            if self.evacuating and self.evacuation_goal.colliderect(self.rect):
                self.evacuated = True
                self.evacuating = False
                self.evacuation_path.clear()
            return
        if self.pause > 0:
            self.pause -= dt
            self.walk_time = 0.0
            return

        delta = self.target - self.pos
        if delta.length_squared() < 4:
            self.pause = self.rng.uniform(1.2, 3.2)
            self._pick_target(walls, collision)
            self.walk_time = 0.0
            return

        self.facing = delta.normalize()
        step = self.facing * min(self.walk_speed * dt, delta.length())
        proposed = self.pos + step
        probe = self.rect.copy()
        probe.center = (round(proposed.x), round(proposed.y))
        if (any(probe.colliderect(wall) for wall in walls)
                or (collision and collision.is_blocked(probe))):
            self.pause = 0.5
            self._pick_target(walls, collision)
            return
        self.pos = proposed
        self.rect.center = (round(self.pos.x), round(self.pos.y))
        self.walk_time += dt

    def draw(self, surface, camera, carried_by=None):
        if self.carried and carried_by is None:
            return
        screen_rect = camera.apply(carried_by.rect if carried_by else self.rect)
        zoom = camera.zoom
        if self.walk_sheet:
            if abs(self.facing.x) > abs(self.facing.y):
                direction = "right" if self.facing.x >= 0 else "left"
            else:
                direction = "down" if self.facing.y >= 0 else "up"
            moving = self.walk_time > 0
            phase = int(self.walk_time * self.walk_sheet.fps) % 4 if moving else 0
            art = self.walk_sheet.image_for(direction, moving, phase)
            draw_size = (max(1, round(self.WORLD_SPRITE_SIZE[0] * zoom)),
                         max(1, round(self.WORLD_SPRITE_SIZE[1] * zoom)))
            if art.get_size() != draw_size:
                art = pygame.transform.scale(art, draw_size)
            shadow = pygame.Rect(0, 0, max(8, round(16 * zoom)), max(3, round(5 * zoom)))
            shadow.midbottom = (screen_rect.centerx, screen_rect.bottom + max(1, round(2 * zoom)))
            pygame.draw.ellipse(surface, (28, 58, 48), shadow)
            surface.blit(art, art.get_rect(midbottom=(screen_rect.centerx,
                                                       screen_rect.bottom + round(2 * zoom))))
            return
        if self.reference_sprite:
            draw_size = (max(1, round(20 * zoom)), max(1, round(29 * zoom)))
            art = pygame.transform.scale(self.reference_sprite, draw_size)
            if self.facing.x < -0.15:
                art = pygame.transform.flip(art, True, False)
            bob = round(1 * zoom) if self.walk_time > 0 and int(self.walk_time * 8) % 2 else 0
            shadow = pygame.Rect(0, 0, max(8, round(16 * zoom)), max(3, round(5 * zoom)))
            shadow.midbottom = (screen_rect.centerx, screen_rect.bottom + max(1, round(2 * zoom)))
            pygame.draw.ellipse(surface, (28, 58, 48), shadow)
            surface.blit(art, art.get_rect(midbottom=(screen_rect.centerx,
                                                       screen_rect.bottom + round(2 * zoom) - bob)))
            return

        sprite = pygame.Surface((24, 36), pygame.SRCALPHA)
        x = 12
        y = 34
        walking = self.walk_time > 0
        stride = (1 if int(self.walk_time * 8) % 2 else -1) if walking else 0
        bob = (1 if int(self.walk_time * 8) % 2 else 0) if walking else int(math.sin(self.time * 2) > 0)

        # A crisp, 20x24 person silhouette, with skin, hair, clothes, shoes,
        # small facial features and a unique silhouette for community leaders.
        pygame.draw.ellipse(sprite, (25, 39, 31), (x - 8, y - 3, 16, 5))
        pygame.draw.rect(sprite, (54, 48, 43), (x - 5 + stride, y - 10, 4, 7))
        pygame.draw.rect(sprite, (54, 48, 43), (x + 1 - stride, y - 10, 4, 7))
        pygame.draw.rect(sprite, self.pants, (x - 5 + stride, y - 15 + bob, 4, 6))
        pygame.draw.rect(sprite, self.pants, (x + 1 - stride, y - 15 + bob, 4, 6))
        pygame.draw.rect(sprite, (227, 179, 124), (x - 6, y - 19 + bob, 12, 7))
        pygame.draw.rect(sprite, self.color, (x - 6, y - 20 + bob, 12, 8))
        pygame.draw.rect(sprite, (max(0, self.color[0] - 40), max(0, self.color[1] - 35), max(0, self.color[2] - 35)),
                         (x - 6, y - 13 + bob, 12, 2))

        arm_shift = stride if walking else int(math.sin(self.time * 2) * 1)
        pygame.draw.rect(sprite, self.color, (x - 9, y - 19 + bob + arm_shift, 3, 7))
        pygame.draw.rect(sprite, self.color, (x + 6, y - 19 + bob - arm_shift, 3, 7))
        pygame.draw.rect(sprite, self.skin, (x - 9, y - 13 + bob + arm_shift, 3, 2))
        pygame.draw.rect(sprite, self.skin, (x + 6, y - 13 + bob - arm_shift, 3, 2))

        head = pygame.Rect(x - 5, y - 28 + bob, 10, 9)
        pygame.draw.rect(sprite, self.skin, head)
        pygame.draw.rect(sprite, self.hair, (x - 6, head.y - 2, 12, 4))
        pygame.draw.rect(sprite, self.hair, (x - 6, head.y + 1, 2, 5))
        pygame.draw.rect(sprite, self.hair, (x + 4, head.y + 1, 2, 5))

        if self.facing.y >= 0:
            pygame.draw.rect(sprite, (39, 34, 33), (x - 3, head.y + 4, 1, 1))
            pygame.draw.rect(sprite, (39, 34, 33), (x + 2, head.y + 4, 1, 1))
        elif abs(self.facing.x) > abs(self.facing.y):
            eye_x = x + 2 if self.facing.x > 0 else x - 3
            pygame.draw.rect(sprite, (39, 34, 33), (eye_x, head.y + 4, 1, 1))

        # Give named villagers distinct professions, ages and silhouettes.
        # Shared body proportions keep the cast coherent while accessories
        # make each person easy to recognize during a rescue.
        if self.style == "responder":
            pygame.draw.rect(sprite, (244, 182, 61), (x - 7, y - 20 + bob, 14, 2))
            pygame.draw.rect(sprite, (247, 217, 121), (x - 2, y - 19 + bob, 4, 7))
            pygame.draw.rect(sprite, (47, 80, 87), (x + 4, y - 20 + bob, 3, 5))
            pygame.draw.rect(sprite, (224, 197, 118), (x - 6, head.y - 3, 12, 3))
        elif self.style == "captain":
            pygame.draw.rect(sprite, (61, 87, 69), (x - 7, y - 20 + bob, 14, 2))
            pygame.draw.rect(sprite, (49, 70, 58), (x - 5, head.y - 4, 10, 3))
            pygame.draw.rect(sprite, (233, 193, 87), (x - 1, head.y - 3, 2, 2))
            pygame.draw.rect(sprite, (243, 211, 119), (x + 3, y - 17 + bob, 2, 2))
        elif self.style == "elder_woman":
            pygame.draw.circle(sprite, self.hair, (x + 6, head.y + 2), 3)
            pygame.draw.rect(sprite, (235, 200, 135), (x - 6, head.y - 2, 12, 2))
            pygame.draw.rect(sprite, (243, 228, 198), (x - 3, head.y + 5, 2, 1))
            pygame.draw.rect(sprite, (243, 228, 198), (x + 2, head.y + 5, 2, 1))
            pygame.draw.rect(sprite, (204, 178, 139), (x - 7, y - 12 + bob, 14, 2))
        elif self.style == "elder_man":
            pygame.draw.rect(sprite, self.hair, (x - 6, head.y - 2, 12, 3))
            pygame.draw.rect(sprite, (192, 183, 163), (x - 4, head.y + 5, 8, 2))
            pygame.draw.rect(sprite, (243, 228, 198), (x - 3, head.y + 5, 2, 1))
            pygame.draw.rect(sprite, (243, 228, 198), (x + 2, head.y + 5, 2, 1))
        elif self.style == "adult_woman":
            pygame.draw.rect(sprite, self.hair, (x + 5, head.y, 3, 10))
            pygame.draw.rect(sprite, (223, 192, 141), (x - 6, head.y - 1, 12, 2))
            pygame.draw.rect(sprite, (242, 225, 185), (x - 5, y - 17 + bob, 2, 2))
        elif self.style == "farmer":
            pygame.draw.rect(sprite, (104, 75, 43), (x - 8, head.y - 2, 16, 2))
            pygame.draw.rect(sprite, (121, 86, 49), (x - 5, head.y - 5, 10, 3))
            pygame.draw.rect(sprite, (218, 190, 132), (x - 4, y - 13 + bob, 8, 2))
        elif self.style == "parent":
            pygame.draw.rect(sprite, (78, 82, 116), (x - 7, y - 17 + bob, 2, 8))
            pygame.draw.rect(sprite, (78, 82, 116), (x + 5, y - 17 + bob, 2, 8))
            pygame.draw.rect(sprite, (226, 210, 163), (x - 5, head.y - 1, 10, 2))
        else:  # neighborhood volunteer
            pygame.draw.rect(sprite, (72, 115, 99), (x - 7, y - 18 + bob, 3, 7))
            pygame.draw.rect(sprite, (72, 115, 99), (x + 4, y - 18 + bob, 3, 7))
            pygame.draw.rect(sprite, (238, 207, 119), (x - 2, head.y - 3, 4, 2))

        if self.is_leader:
            pygame.draw.rect(sprite, (229, 190, 92), (x - 7, head.y - 3, 14, 2))
            pygame.draw.rect(sprite, (178, 121, 59), (x - 4, head.y - 5, 8, 2))

        if self.rescued:
            badge = pygame.Rect(x + 5, head.y - 3, 8, 8)
            pygame.draw.circle(sprite, (244, 248, 220), badge.center, 5)
            pygame.draw.circle(sprite, (55, 155, 92), badge.center, 5, 1)
            pygame.draw.lines(sprite, (45, 128, 73), False,
                              [(badge.x + 2, badge.y + 4), (badge.x + 3, badge.y + 5), (badge.x + 6, badge.y + 2)], 1)
        # Match the player sprite scale and keep buildings visibly larger.
        # The hand-drawn pose is authored at 24x36, then reduced for world use.
        sprite = pygame.transform.scale(sprite, self.WORLD_SPRITE_SIZE)
        scale = zoom * (0.78 if carried_by else 1.0)
        scaled = pygame.transform.scale(sprite, (round(sprite.get_width() * scale),
                                                 round(sprite.get_height() * scale)))
        if carried_by:
            anchor = (screen_rect.centerx + round(6 * zoom), screen_rect.y + round(12 * zoom))
        else:
            anchor = (screen_rect.centerx, screen_rect.bottom + round(2 * zoom))
        surface.blit(scaled, scaled.get_rect(midbottom=anchor))
