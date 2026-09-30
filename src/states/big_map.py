import pygame

from src.ui import theme
from src.core import settings
from src.core.event_bus import EventBus
from src.entities.mascot import Mascot
from src.entities.npc import NPC
from src.entities.player import Player
from src.hazards.debris import Debris
from src.hazards.rain import Rain
from src.hazards.wind import Wind
from src.states.base_state import BaseState
from src.states.game_over import GameOver
from src.states.stage_complete import StageComplete
from src.systems.quest_system import QuestSystem
from src.ui.choice_box import ChoiceBox
from src.ui.dialogue_box import DialogueBox
from src.utils.data_loader import load_json
from src.world.camera import Camera

TILE = 16

# (below this danger value, name, color)
LEVELS = [
    (25, "NORMAL", (110, 230, 130)),
    (50, "WATCH", (255, 220, 80)),
    (75, "WARNING", (255, 150, 50)),
    (101, "CRITICAL", (255, 80, 80)),
]


class BigMap(BaseState):
    def __init__(self, game, stage_id="typhoon"):
        super().__init__(game)
        self.stage_id = stage_id
        self.data = load_json(f"data/stages/{stage_id}.json")
        self.font = theme.get_font("tiny")

        w, h = self.data["map_size"]
        self.map_width, self.map_height = w, h
        self.walls = [
            pygame.Rect(0, 0, w, 8), pygame.Rect(0, h - 8, w, 8),
            pygame.Rect(0, 0, 8, h), pygame.Rect(w - 8, 0, 8, h),
        ] + [pygame.Rect(*r) for r in self.data["walls"]]

        character = game.session.character
        sx, sy = self.data["player_start"]
        self.player = Player(
            sx, sy, speed=character["speed"], max_health=character["max_health"]
        )
        self.player.color = tuple(character["color"])
        self.camera = Camera(w, h)

        self.npcs = [NPC(n) for n in self.data["npcs"]]
        self.items = [
            {**i, "rect": pygame.Rect(i["pos"][0], i["pos"][1], 8, 8)}
            for i in self.data["items"]
        ]
        self.areas = [{**a, "rect": pygame.Rect(*a["rect"])} for a in self.data["areas"]]

        self.events = EventBus()
        self.quests = QuestSystem(self.data["quests"], self.events)
        self.events.subscribe("quest_completed", self.on_quest_completed)
        self.events.subscribe("item_collected", self.on_item)
        self.dialogue = DialogueBox(self.font)
        self.choice = ChoiceBox(self.font)

        mascot_config = load_json("data/mascot.json")
        self.mascot = Mascot(
            mascot_config, self.data["mascot"], self.events,
            self.quests, self.font, self.player.rect.center,
        )

        # Hazards
        hz = self.data["hazards"]
        self.ramp = hz["danger_ramp_seconds"]
        self.start_delay = hz["hazard_start_seconds"]
        self.rain = Rain(hz["rain"])
        self.wind = Wind(hz["wind"], self.events)
        self.debris = Debris(hz["debris"], (w, h), self.events)
        self.elapsed = 0.0      # drives the danger meter (choices can add to it)
        self.play_time = 0.0    # real time played, shown in results
        self.last_level = "NORMAL"

        # Run statistics
        self.items_found = 0
        self.items_total = len(self.items)
        self.bonus_points = 0
        self.choice_flags = []
        self.consequences = []

        self.toast = ""
        self.toast_timer = 0.0
        self.finished = False
        self.finish_timer = 0.0

    # ---------- danger meter ----------
    def danger(self):
        return min(100.0, self.elapsed / self.ramp * 100)

    def level_of(self, danger):
        for limit, name, color in LEVELS:
            if danger < limit:
                return name, color
        return LEVELS[-1][1], LEVELS[-1][2]

    # ---------- events ----------
    def on_quest_completed(self, title, **_):
        self.toast = f"QUEST DONE: {title}"
        self.toast_timer = 3.0

    def on_item(self, **_):
        self.items_found += 1

    def nearby_npc(self):
        for npc in self.npcs:
            if npc.is_near(self.player.rect):
                return npc
        return None

    def talk(self, npc):
        lines = npc.get_lines()
        first_time = not npc.talked
        npc.talked = True

        def finish():
            if first_time:
                self.events.emit("npc_talked", npc_id=npc.id)
                if npc.choice:
                    self.choice.open(
                        npc.name, npc.choice["prompt"],
                        npc.choice["options"], self.on_choice,
                    )

        self.dialogue.open(npc.name, lines, finish)

    def on_choice(self, option):
        self.choice_flags.append(option["flag"])
        self.consequences.append(option["consequence"])
        self.elapsed += option.get("time_cost", 0)
        self.bonus_points += option.get("points", 0)
        self.toast = option["result"]
        self.toast_timer = 4.0
        if "mascot" in option:
            self.mascot.say(option["mascot"], 6)
        self.events.emit("choice_made", flag=option["flag"])

    # ---------- game flow ----------
    def game_over(self):
        self.game.state_manager.push(GameOver(self.game, self.retry))

    def retry(self):
        manager = self.game.state_manager
        manager.pop()                                     # close the top screen
        manager.change(BigMap(self.game, self.stage_id))  # restart the stage

    def build_stats(self):
        p = self.player
        time_s = int(self.play_time)
        score = max(0, 1000 - p.damage_taken * 5 - time_s * 2)
        score += self.items_found * 100 + self.bonus_points
        all_quests = self.quests.all_done()
        return {
            "stage_id": self.stage_id,
            "time": time_s,
            "damage": p.damage_taken,
            "items_found": self.items_found,
            "items_total": self.items_total,
            "quests_done": self.quests.done_count(),
            "quests_total": len(self.quests.quests),
            "score": score,
            "perfect": (p.damage_taken == 0 and all_quests
                        and self.items_found == self.items_total),
            "choices": self.choice_flags,
            "consequences": self.consequences,
            "lessons": self.data.get("lessons", []),
        }

    def show_results(self):
        stats = self.build_stats()
        self.game.session.complete_stage(self.stage_id)
        self.game.session.record_run(self.stage_id, stats)
        self.game.state_manager.push(StageComplete(self.game, stats, self.retry))

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return
        if self.choice.active:
            self.choice.handle_key(event.key)
            return
        if self.dialogue.active:
            if event.key in (pygame.K_e, pygame.K_RETURN, pygame.K_SPACE):
                self.dialogue.advance()
            return
        if event.key == pygame.K_ESCAPE:
            self.game.state_manager.pop()
        elif event.key in (pygame.K_e, pygame.K_RETURN, pygame.K_SPACE):
            npc = self.nearby_npc()
            if npc:
                self.talk(npc)
        elif event.key == pygame.K_h:
            self.mascot.ask_hint()

    # ---------- update ----------
    def update(self, dt):
        self.dialogue.update(dt)
        if self.toast_timer > 0:
            self.toast_timer -= dt

        if self.finished:
            self.finish_timer -= dt
            if self.finish_timer <= 0:
                self.show_results()
            return

        self.mascot.update(dt, self.player.rect)

        if self.dialogue.active or self.choice.active:
            return  # everything freezes while talking or choosing

        self.play_time += dt
        self.elapsed += dt
        danger = self.danger()
        level, _ = self.level_of(danger)
        if level != self.last_level:
            self.last_level = level
            self.events.emit("danger_level", level=level)

        self.rain.update(dt, self.wind.push.x)
        if self.elapsed > self.start_delay:
            self.wind.update(dt, danger)
            self.debris.update(dt, self.player, danger)

        self.player.update(dt, self.walls, self.wind.push)
        self.camera.follow(self.player.rect)

        for item in self.items[:]:
            if self.player.rect.colliderect(item["rect"]):
                self.items.remove(item)
                self.events.emit("item_collected", item_id=item["id"])

        for area in self.areas:
            if self.player.rect.colliderect(area["rect"]):
                self.events.emit("area_reached", area_id=area["id"])

        if self.quests.all_done():
            self.finished = True
            self.finish_timer = 1.5
            self.toast = "STAGE COMPLETE!"
            self.toast_timer = 1.5
        elif self.player.health <= 0:
            self.game_over()

    # ---------- draw ----------
    def draw(self, surface):
        surface.fill((40, 90, 60))
        cam = self.camera
        ox, oy = int(cam.offset.x), int(cam.offset.y)

        for row in range(oy // TILE, oy // TILE + settings.INTERNAL_HEIGHT // TILE + 2):
            for col in range(ox // TILE, ox // TILE + settings.INTERNAL_WIDTH // TILE + 2):
                if (row + col) % 2 == 0:
                    tile = pygame.Rect(col * TILE, row * TILE, TILE, TILE)
                    pygame.draw.rect(surface, (48, 100, 68), cam.apply(tile))

        for area in self.areas:
            r = cam.apply(area["rect"])
            pygame.draw.rect(surface, tuple(area["color"]), r, 2)
            label = self.font.render(area["name"].upper(), False, (255, 255, 255))
            surface.blit(label, (r.x, r.y - 10))

        for wall in self.walls:
            pygame.draw.rect(surface, (90, 70, 60), cam.apply(wall))

        for item in self.items:
            pygame.draw.rect(surface, tuple(item["color"]), cam.apply(item["rect"]))
            pygame.draw.rect(surface, (255, 255, 255), cam.apply(item["rect"]), 1)

        for npc in self.npcs:
            npc.draw(surface, cam)

        self.debris.draw(surface, cam)
        self.player.draw(surface, cam)
        self.mascot.draw(surface, cam, show_bubble=not (self.dialogue.active or self.choice.active))

        npc = self.nearby_npc()
        if npc and not self.dialogue.active and not self.choice.active:
            r = cam.apply(npc.rect)
            tip = self.font.render("E: TALK", False, (255, 255, 120))
            surface.blit(tip, tip.get_rect(midbottom=(r.centerx, r.y - 2)))

        self.rain.draw(surface, cam.apply(self.player.rect).center)
        self.wind.draw(surface)

        if self.player.invuln > 0.7:   # red flash when hit
            flash = pygame.Surface(
                (settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT), pygame.SRCALPHA
            )
            flash.fill((255, 0, 0, 60))
            surface.blit(flash, (0, 0))

        self.draw_status(surface)
        self.draw_quest_hud(surface)
        self.dialogue.draw(surface)
        self.choice.draw(surface)

        if self.toast_timer > 0:
            r = theme.draw_text(surface, self.toast, (160, 46), "tiny", theme.HONEY,
                                shadow=False, anchor="center")
            theme.draw_panel(surface, r.inflate(14, 8), accent=theme.HONEY)
            theme.draw_text(surface, self.toast, r.center, "tiny", theme.HONEY,
                            shadow=False, anchor="center")

    def draw_status(self, surface):
        p = self.player
        theme.draw_panel(surface, (4, 4, 124, 32), alpha=220)
        theme.draw_text(surface, "HP", (9, 7), "tiny", theme.CREAM)
        theme.draw_bar(surface, (28, 9, 92, 7), p.health, p.max_health, theme.CORAL)

        danger = self.danger()
        level, color = self.level_of(danger)
        theme.draw_text(surface, "RISK", (9, 19), "tiny", theme.CREAM)
        theme.draw_bar(surface, (28, 21, 60, 7), danger, 100, color)
        theme.draw_text(surface, level, (92, 19), "tiny", color)

    def draw_quest_hud(self, surface):
        quests = self.quests.quests
        w, h = 146, 20 + len(quests) * 11
        x = settings.INTERNAL_WIDTH - w - 4
        theme.draw_panel(surface, (x, 4, w, h),
                         title=f"QUESTS {self.quests.done_count()}/{len(quests)}",
                         alpha=220)
        for i, q in enumerate(quests):
            y = 22 + i * 11
            box = pygame.Rect(x + 6, y + 1, 6, 6)
            if q["done"]:
                pygame.draw.rect(surface, theme.SAGE, box)
                pygame.draw.lines(surface, theme.NIGHT, False,
                                  [(box.x + 1, box.y + 3), (box.x + 2, box.y + 4), (box.x + 4, box.y + 1)])
            else:
                pygame.draw.rect(surface, theme.CREAM_DIM, box, 1)
            color = theme.SAGE if q["done"] else theme.CREAM
            theme.draw_text(surface, q["title"], (x + 16, y - 1), "tiny", color)