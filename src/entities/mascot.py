import math

import pygame

from src.core import settings
from src.ui import pixel_art, theme
from src.utils.helpers import wrap_text
class Mascot:
    IDLE_DELAY = 20  # seconds without progress before it offers a hint

    def __init__(self, config, stage_hints, events, quests, font, start):
        self.name = config["name"]
        self.color = tuple(config["color"])
        self.hints = stage_hints
        self.quests = quests
        self.font = font

        self.pos = pygame.Vector2(start)
        self.rect = pygame.Rect(0, 0, 10, 10)
        self.rect.center = start
        self.time = 0.0
        self.idle_timer = 0.0
        self.bubble = ""
        self.bubble_timer = 0.0
        self.hint_cursor = -1

        events.subscribe("quest_completed", self.on_quest_completed)
        events.subscribe("item_collected", self.on_progress)
        self.say(stage_hints["intro"], 7)
        self.sprite = pixel_art.mascot_sprite(self.color)
        self.wind_warned = False
        events.subscribe("wind_warning", self.on_wind)
        events.subscribe("danger_level", self.on_danger)

    # ---------- speech ----------
    def say(self, text, seconds=5):
        self.bubble = text
        self.bubble_timer = seconds
        self.idle_timer = 0.0

    def next_hint(self):
        pending = [q for q in self.quests.quests if not q["done"]]
        if not pending:
            return "All done! Head back to the world map."
        self.hint_cursor = (self.hint_cursor + 1) % len(pending)
        quest = pending[self.hint_cursor]
        return self.hints["quests"].get(quest["id"], quest["title"])

    def ask_hint(self):
        self.say(self.next_hint(), 6)

    # ---------- event reactions ----------
    def on_progress(self, **_):
        self.idle_timer = 0.0

    def on_wind(self, **_):
        if not self.wind_warned:          # only warn the first time
            self.wind_warned = True
            self.say("Strong wind! It will push you. Keep moving!", 4)
    def on_danger(self, level, **_):
        if level in ("WARNING", "CRITICAL"):
            self.say(f"Danger is {level}! Hurry and finish your quests!", 5)

    def on_quest_completed(self, **_):
        if self.quests.all_done():
            self.say("We did it! Great job staying safe!", 5)
        else:
            self.say("Nice work! " + self.next_hint(), 6)

    # ---------- update / draw ----------
    def update(self, dt, player_rect):
        self.time += dt

        # Glide toward a spot behind-left of the player.
        target = pygame.Vector2(player_rect.centerx - 16, player_rect.centery - 4)
        self.pos += (target - self.pos) * min(1.0, 5 * dt)
        self.rect.center = (round(self.pos.x), round(self.pos.y))

        if self.bubble_timer > 0:
            self.bubble_timer -= dt
        self.idle_timer += dt
        if self.idle_timer > self.IDLE_DELAY:
            self.say(self.next_hint(), 6)

    def draw(self, surface, camera, show_bubble=True, avoid_rects=()):
        bob = int(math.sin(self.time * 4) * 1.5)
        r = camera.apply(self.rect.move(0, bob))

        surface.blit(self.sprite, r.topleft)

        if self.bubble_timer > 0 and show_bubble:
            self.draw_bubble(surface, camera, avoid_rects)

    def draw_bubble(self, surface, camera, avoid_rects=()):
        if self.bubble_timer <= 0 or not self.bubble:
            return
        bob = int(math.sin(self.time * 4) * 1.5)
        r = camera.apply(self.rect.move(0, bob))
        lines = wrap_text(self.bubble, self.font, 158)[:5]
        w = min(170, max(self.font.size(line)[0] for line in lines) + 12)
        h = len(lines) * 10 + 8
        x = max(4, min(r.centerx - w // 2, settings.INTERNAL_WIDTH - w - 4))
        y = max(4, r.y - h - 4)
        box = pygame.Rect(x, y, w, h)
        if any(box.colliderect(avoid) for avoid in avoid_rects):
            below_y = min(settings.INTERNAL_HEIGHT - h - 4, r.bottom + 8)
            below = pygame.Rect(x, below_y, w, h)
            if not any(below.colliderect(avoid) for avoid in avoid_rects):
                box = below
            else:
                for offset in (-w - 12, 18):
                    other_x = max(4, min(r.centerx + offset, settings.INTERNAL_WIDTH - w - 4))
                    other = pygame.Rect(other_x, y, w, h)
                    if not any(other.colliderect(avoid) for avoid in avoid_rects):
                        box = other
                        break
        pygame.draw.rect(surface, (10, 15, 26), box.inflate(2, 2))
        pygame.draw.rect(surface, (250, 250, 240), box)
        pygame.draw.rect(surface, self.color, box, 1)
        for i, line in enumerate(lines):
            theme.draw_text(surface, line, (box.x + 6, box.y + 4 + i * 10),
                            self.font, (30, 30, 50), shadow=False)
        tail_x = max(box.x + 8, min(r.centerx, box.right - 8))
        if box.bottom < r.top:
            pygame.draw.polygon(surface, (250, 250, 240),
                                [(tail_x - 4, box.bottom - 1), (tail_x + 4, box.bottom - 1),
                                 (tail_x, box.bottom + 5)])
        else:
            pygame.draw.polygon(surface, (250, 250, 240),
                                [(tail_x - 4, box.y + 1), (tail_x + 4, box.y + 1),
                                 (tail_x, box.y - 5)])

    def draw_tip(self, surface):
        """Speech is drawn beside Tarsi, not as a fixed overlay card."""
        return
