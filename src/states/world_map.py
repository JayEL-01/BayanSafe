import math

import pygame
import random

from src.core import settings
from src.states.base_state import BaseState
from src.states.big_map import BigMap
from src.utils.data_loader import BASE_DIR, load_json
from src.utils.helpers import wrap_text
from src.world.camera import Camera

GOLD = (255, 220, 80)
GRAY = (130, 130, 140)
GREEN = (90, 220, 120)
DARK = (15, 25, 55)


# ---------------------------------------------------------------
# Placeholder art (only used if assets/images/world/world_map.png
# does not exist yet)
# ---------------------------------------------------------------
def make_blob(center, radius, seed, points=16):
    """A lumpy island outline. Same seed = same shape every time."""
    rng = random.Random(seed)
    cx, cy = center
    pts = []
    for i in range(points):
        angle = 2 * math.pi * i / points
        r = radius * rng.uniform(0.75, 1.05)
        pts.append((cx + math.cos(angle) * r, cy + math.sin(angle) * r * 0.8))
    return pts


def draw_decoration(surf, node):
    """A tiny themed drawing on each stage island."""
    cx, cy = node["pos"]
    cy -= 12
    kind = node["id"]

    if kind == "typhoon":
        white = (225, 235, 250)
        pygame.draw.circle(surf, white, (cx, cy), 16, 2)
        pygame.draw.circle(surf, white, (cx, cy), 10, 2)
        pygame.draw.circle(surf, white, (cx, cy), 4)

    elif kind == "flood":
        pygame.draw.rect(surf, (230, 220, 200), (cx - 7, cy - 6, 14, 12))
        pygame.draw.polygon(surf, (180, 60, 60),
                            [(cx - 9, cy - 6), (cx, cy - 15), (cx + 9, cy - 6)])
        for dx in (-24, 12):
            pygame.draw.ellipse(surf, (40, 100, 180), (cx + dx, cy + 8, 16, 7))

    elif kind == "earthquake":
        pygame.draw.rect(surf, (200, 190, 170), (cx - 22, cy - 10, 14, 16))
        pygame.draw.lines(surf, (40, 25, 15), False,
                          [(cx + 6, cy - 18), (cx + 12, cy - 9),
                           (cx + 5, cy), (cx + 11, cy + 9)], 2)

    elif kind == "volcano":
        pygame.draw.circle(surf, (140, 130, 130), (cx - 2, cy - 24), 5)
        pygame.draw.circle(surf, (140, 130, 130), (cx + 6, cy - 28), 4)
        pygame.draw.polygon(surf, (70, 45, 40),
                            [(cx - 20, cy + 6), (cx, cy - 18), (cx + 20, cy + 6)])
        pygame.draw.polygon(surf, (255, 110, 30),
                            [(cx - 6, cy - 11), (cx, cy - 18), (cx + 6, cy - 11)])

    elif kind == "wildfire":
        base = cy + 6
        for dx, h in ((-16, 18), (0, 26), (16, 16)):
            pygame.draw.polygon(surf, (240, 90, 20),
                                [(cx + dx - 7, base), (cx + dx, base - h), (cx + dx + 7, base)])
            pygame.draw.polygon(surf, (255, 220, 70),
                                [(cx + dx - 3, base), (cx + dx, base - h // 2), (cx + dx + 3, base)])


def build_background(data):
    w, h = data["size"]
    surf = pygame.Surface((w, h))
    surf.fill((22, 50, 105))

    # ocean wave dashes
    for row, y in enumerate(range(6, h, 10)):
        for x in range((row % 2) * 7, w, 14):
            pygame.draw.line(surf, (34, 70, 132), (x, y), (x + 5, y))

    islands = data.get("decor_islands", []) + data["nodes"]
    # Draw ALL shores first, then ALL land, so overlapping islands merge.
    for isl in islands:
        shore = tuple(min(255, c + 45) for c in isl["land"])
        pygame.draw.polygon(surf, shore, make_blob(isl["pos"], isl["radius"] + 5, isl["seed"]))
    for isl in islands:
        pygame.draw.polygon(surf, tuple(isl["land"]), make_blob(isl["pos"], isl["radius"], isl["seed"]))

    for node in data["nodes"]:
        draw_decoration(surf, node)
    return surf


# ---------------------------------------------------------------
# Route helpers
# ---------------------------------------------------------------
def path_length(pts):
    return sum(math.dist(a, b) for a, b in zip(pts, pts[1:]))


def point_at(pts, dist):
    """Position after travelling `dist` pixels along a polyline."""
    for a, b in zip(pts, pts[1:]):
        seg = math.dist(a, b)
        if seg > 0 and dist <= seg:
            t = dist / seg
            return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
        dist -= seg
    return pts[-1]


class WorldMap(BaseState):
    SPEED = 90  # marker speed in pixels per second
    ZOOMS = [2 / 3, 1.0, 1.5] 

    def __init__(self, game):
        super().__init__(game)
        self.data = load_json("data/world_map.json")
        self.nodes = self.data["nodes"]

        self.background = self._load_background()
        self.map_w, self.map_h = self.background.get_size()
        

        # route i goes from node i to node i+1
        self.routes = []
        for i, waypoints in enumerate(self.data["routes"]):
            pts = [tuple(self.nodes[i]["pos"])]
            pts += [tuple(p) for p in waypoints]
            pts.append(tuple(self.nodes[i + 1]["pos"]))
            self.routes.append(pts)
        self.route_dots = [
            [point_at(r, d) for d in range(0, int(path_length(r)), 6)]
            for r in self.routes
        ]

        self.current = 0
        self.pos = pygame.Vector2(self.nodes[0]["pos"])
        self.queue = []
        self.travel = None
        self.time = 0.0

        self.med = pygame.font.Font(None, 16)
        self.small = pygame.font.Font(None, 12)
        self.message = ""
        self.message_timer = 0.0

        self.zoom_index = 0
        self.bg_cache = {}
        self._apply_zoom()

    def _apply_zoom(self):
        self.zoom = self.ZOOMS[self.zoom_index]
        w, h = round(self.map_w * self.zoom), round(self.map_h * self.zoom)
        if self.zoom not in self.bg_cache:
            if self.zoom == 1:
                self.bg_cache[self.zoom] = self.background
            else:
                self.bg_cache[self.zoom] = pygame.transform.scale(self.background, (w, h))
        self.scaled_bg = self.bg_cache[self.zoom]
        self.camera = Camera(w, h)
        self._follow()

    def _follow(self):
        self.camera.follow(
            pygame.Rect(int(self.pos.x * self.zoom), int(self.pos.y * self.zoom), 1, 1)
        )

    def to_screen(self, x, y):
        """World position -> position on the screen."""
        return (
            int(x * self.zoom - self.camera.offset.x),
            int(y * self.zoom - self.camera.offset.y),
        )

    def change_zoom(self, step):
        new = max(0, min(len(self.ZOOMS) - 1, self.zoom_index + step))
        if new != self.zoom_index:
            self.zoom_index = new
            self._apply_zoom()

    # ---------- setup ----------
    def _load_background(self):
        path = BASE_DIR / self.data["background"]
        if path.exists():
            return pygame.image.load(str(path)).convert()
        return build_background(self.data)

    # ---------- movement ----------
    def _start_leg(self):
        if not self.queue:
            self.travel = None
            return
        target = self.queue.pop(0)
        if target > self.current:
            pts = self.routes[self.current]
        else:
            pts = list(reversed(self.routes[target]))
        self.travel = {"pts": pts, "length": path_length(pts), "dist": 0.0, "target": target}

    def go_to(self, index):
        if self.travel or index == self.current:
            return
        if index < 0 or index >= len(self.nodes):
            return
        step = 1 if index > self.current else -1
        for n in range(self.current + step, index + step, step):
            if not self.game.session.is_unlocked(self.nodes[n]["id"]):
                self.message = f"LOCKED: complete {self.nodes[n - 1]['name']} first."
                self.message_timer = 2.5
                break
            self.queue.append(n)
        self._start_leg()

    def enter_stage(self):
        if self.travel:
            return
        node = self.nodes[self.current]
        if not (BASE_DIR / f"data/stages/{node['id']}.json").exists():
            self.message = f"{node['name']} stage is coming soon."
            self.message_timer = 2.5
            return
        self.game.state_manager.push(BigMap(self.game, node["id"]))
        
    def click_node(self, i):
        if i == self.current:
            self.enter_stage()
        else:
            self.go_to(i)

    # ---------- events ----------
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RIGHT, pygame.K_d):
                self.go_to(self.current + 1)
            elif event.key in (pygame.K_LEFT, pygame.K_a):
                self.go_to(self.current - 1)
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.enter_stage()
            elif event.key == pygame.K_z:  # cycle zoom
                self.zoom_index = (self.zoom_index + 1) % len(self.ZOOMS)
                self._apply_zoom()
            elif event.key in (pygame.K_EQUALS, pygame.K_PLUS):
                self.change_zoom(1)
            elif event.key == pygame.K_MINUS:
                self.change_zoom(-1)
            elif event.key == pygame.K_ESCAPE:
                self.game.state_manager.pop()

        elif event.type == pygame.MOUSEWHEEL:
            self.change_zoom(1 if event.y > 0 else -1)

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            cx, cy = self.game.to_canvas_pos(event.pos)
            wx = (cx + self.camera.offset.x) / self.zoom
            wy = (cy + self.camera.offset.y) / self.zoom
            print(f"Clicked world position: [{int(wx)}, {int(wy)}]")
            for i, node in enumerate(self.nodes):
                sx, sy = self.to_screen(*node["pos"])
                if math.dist((cx, cy), (sx, sy)) < 12:
                    self.click_node(i)
                    break

    # ---------- update ----------
    def update(self, dt):
        self.time += dt
        if self.message_timer > 0:
            self.message_timer -= dt

        if self.travel:
            t = self.travel
            t["dist"] += self.SPEED * dt
            if t["dist"] >= t["length"]:
                self.current = t["target"]
                self.pos.update(self.nodes[self.current]["pos"])
                self._start_leg()
            else:
                self.pos.update(point_at(t["pts"], t["dist"]))

        self._follow()

    # ---------- drawing ----------
    def draw(self, surface):
        surface.fill(DARK)
        ox, oy = int(self.camera.offset.x), int(self.camera.offset.y)
        surface.blit(self.scaled_bg, (-ox, -oy))
        self._draw_routes(surface)
        self._draw_nodes(surface)
        self._draw_marker(surface)
        self._draw_hud(surface)

    def _draw_routes(self, surface):
        session = self.game.session
        for i, dots in enumerate(self.route_dots):
            open_route = session.is_unlocked(self.nodes[i + 1]["id"])
            color = GOLD if open_route else (110, 125, 160)
            for x, y in dots:
                sx, sy = self.to_screen(x, y)
                if 0 <= sx <= settings.INTERNAL_WIDTH and 0 <= sy <= settings.INTERNAL_HEIGHT:
                    pygame.draw.circle(surface, color, (sx, sy), 1)

    def _draw_nodes(self, surface):
        session = self.game.session
        for i, node in enumerate(self.nodes):
            px, py = self.to_screen(*node["pos"])
            if not (-30 <= px <= settings.INTERNAL_WIDTH + 30
                    and -30 <= py <= settings.INTERNAL_HEIGHT + 30):
                continue

            unlocked = session.is_unlocked(node["id"])
            done = node["id"] in session.completed
            color = GREEN if done else GOLD if unlocked else GRAY

            pygame.draw.circle(surface, DARK, (px, py), 9)
            pygame.draw.circle(surface, color, (px, py), 7)

            if done:
                pygame.draw.lines(surface, DARK, False,
                                  [(px - 3, py), (px - 1, py + 3), (px + 4, py - 3)], 2)
            elif unlocked:
                num = self.small.render(str(i + 1), False, DARK)
                surface.blit(num, num.get_rect(center=(px, py)))
            else:  # padlock
                pygame.draw.rect(surface, DARK, (px - 3, py - 1, 7, 5))
                pygame.draw.rect(surface, DARK, (px - 2, py - 5, 5, 5), 1)

            if i == self.current and not self.travel:
                pulse = 11 + int(abs(math.sin(self.time * 3)) * 2)
                pygame.draw.circle(surface, (255, 255, 255), (px, py), pulse, 1)

            label_color = (255, 255, 255) if unlocked else (170, 175, 190)
            name = node["name"].upper()
            shadow = self.small.render(name, False, (0, 0, 0))
            text = self.small.render(name, False, label_color)
            surface.blit(shadow, shadow.get_rect(center=(px + 1, py + 15)))
            surface.blit(text, text.get_rect(center=(px, py + 14)))

    def _draw_marker(self, surface):
        character = self.game.session.character
        color = tuple(character["color"]) if character else (255, 200, 60)
        speed = 8 if self.travel else 3
        bob = math.sin(self.time * speed) * 1.5

        x, y = self.to_screen(self.pos.x, self.pos.y)
        pygame.draw.ellipse(surface, (10, 20, 40), (x - 5, y - 3, 10, 4))
        body = pygame.Rect(x - 4, int(y - 15 + bob), 8, 11)
        pygame.draw.rect(surface, color, body)
        pygame.draw.rect(surface, (255, 255, 255), body, 1)

    def _draw_hud(self, surface):
        session = self.game.session

        # top strip
        strip = pygame.Surface((settings.INTERNAL_WIDTH, 14), pygame.SRCALPHA)
        strip.fill((10, 15, 40, 190))
        surface.blit(strip, (0, 0))
        character = session.character
        who = character["name"].upper() if character else "?"
        surface.blit(self.small.render(f"WORLD MAP  -  {who}", False, (255, 200, 60)), (6, 3))

        x = 180
        for label, color in (("OPEN", GOLD), ("LOCKED", GRAY), ("DONE", GREEN)):
            pygame.draw.circle(surface, color, (x, 7), 3)
            text = self.small.render(label, False, (220, 228, 245))
            surface.blit(text, (x + 6, 3))
            x += text.get_width() + 16

        # bottom info panel
        node = self.nodes[self.current]
        accent = tuple(node["accent"])
        box = pygame.Rect(6, 138, 308, 38)
        panel = pygame.Surface(box.size, pygame.SRCALPHA)
        panel.fill((15, 25, 55, 225))
        surface.blit(panel, box.topleft)
        pygame.draw.rect(surface, accent, box, 1)

        name = self.med.render(node["name"].upper(), False, accent)
        surface.blit(name, (box.x + 6, box.y + 3))
        if node["id"] in session.completed:
            done = self.small.render("DONE", False, GREEN)
            surface.blit(done, (box.x + 12 + name.get_width(), box.y + 5))

        hint = self.small.render("A/D: TRAVEL  ENTER: PLAY  Z: ZOOM", False, (150, 170, 210))
        surface.blit(hint, (box.right - hint.get_width() - 6, box.y + 5))

        if self.message_timer > 0:
            text, color = self.message, (255, 120, 120)
        else:
            text, color = node["blurb"], (255, 255, 255)
        for n, line in enumerate(wrap_text(text, self.small, 292)[:2]):
            surface.blit(self.small.render(line, False, color), (box.x + 6, box.y + 17 + n * 10))