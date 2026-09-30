import random

import pygame


class Debris:
    FALL_TIME = 1.2

    def __init__(self, config, map_size, events):
        self.damage = config["damage"]
        self.min_gap = config["min_interval"]   # seconds between drops at max danger
        self.max_gap = config["max_interval"]   # seconds between drops at zero danger
        self.map_w, self.map_h = map_size
        self.events = events
        self.items = []
        self.spawn_timer = 2.0

    def spawn(self, player):
        x = player.rect.centerx + random.randint(-50, 50)
        y = player.rect.centery + random.randint(-40, 40)
        x = max(20, min(x, self.map_w - 20))
        y = max(20, min(y, self.map_h - 20))
        rect = pygame.Rect(0, 0, 16, 16)
        rect.center = (x, y)
        self.items.append({"rect": rect, "state": "falling", "timer": self.FALL_TIME})

    def update(self, dt, player, danger):
        self.spawn_timer -= dt
        if self.spawn_timer <= 0:
            gap = self.max_gap + (self.min_gap - self.max_gap) * danger / 100
            self.spawn_timer = random.uniform(gap * 0.7, gap * 1.3)
            self.spawn(player)

        for d in self.items[:]:
            d["timer"] -= dt
            if d["state"] == "falling" and d["timer"] <= 0:
                d["state"] = "landed"
                d["timer"] = 0.4
                if player.rect.colliderect(d["rect"]):
                    if player.take_damage(self.damage):
                        self.events.emit("player_damaged", amount=self.damage, source="debris")
            elif d["state"] == "landed" and d["timer"] <= 0:
                self.items.remove(d)

    def draw(self, surface, camera):
        for d in self.items:
            r = camera.apply(d["rect"])
            if d["state"] == "falling":
                progress = 1 - d["timer"] / self.FALL_TIME
                size = int(6 + 10 * progress)
                shadow = pygame.Rect(0, 0, size, size // 2 + 2)
                shadow.center = r.center
                pygame.draw.ellipse(surface, (20, 35, 25), shadow)
                if int(d["timer"] * 8) % 2 == 0:
                    pygame.draw.rect(surface, (255, 80, 60), r, 1)
                obj = pygame.Rect(0, 0, 10, 10)
                obj.center = (r.centerx, r.centery - int(d["timer"] * 140))
                pygame.draw.rect(surface, (120, 90, 60), obj)
                pygame.draw.rect(surface, (60, 45, 30), obj, 1)
            else:
                pygame.draw.rect(surface, (120, 90, 60), r.inflate(-4, -4))
                pygame.draw.rect(surface, (60, 45, 30), r.inflate(-4, -4), 1)