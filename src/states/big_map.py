import pygame

from src.core import settings
from src.core.event_bus import EventBus
from src.entities.player import Player
from src.states.base_state import BaseState
from src.systems.quest_system import QuestSystem
from src.ui.dialogue_box import DialogueBox
from src.utils.data_loader import load_json
from src.world.camera import Camera

TILE = 16


class BigMap(BaseState):
    def __init__(self, game, stage_id="typhoon"):
        super().__init__(game)
        self.stage_id = stage_id
        self.data = load_json(f"data/stages/{stage_id}.json")
        self.font = pygame.font.Font(None, 12)

        w, h = self.data["map_size"]
        self.map_width, self.map_height = w, h
        self.walls = [
            pygame.Rect(0, 0, w, 8), pygame.Rect(0, h - 8, w, 8),
            pygame.Rect(0, 0, 8, h), pygame.Rect(w - 8, 0, 8, h),
        ] + [pygame.Rect(*r) for r in self.data["walls"]]

        character = game.session.character
        sx, sy = self.data["player_start"]
        self.player = Player(sx, sy, speed=character["speed"])
        self.player.color = tuple(character["color"])
        self.camera = Camera(w, h)

        self.npcs = [
            {**n, "rect": pygame.Rect(n["pos"][0], n["pos"][1], 12, 12), "talked": False}
            for n in self.data["npcs"]
        ]
        self.items = [
            {**i, "rect": pygame.Rect(i["pos"][0], i["pos"][1], 8, 8)}
            for i in self.data["items"]
        ]
        self.areas = [{**a, "rect": pygame.Rect(*a["rect"])} for a in self.data["areas"]]

        self.events = EventBus()
        self.quests = QuestSystem(self.data["quests"], self.events)
        self.events.subscribe("quest_completed", self.on_quest_completed)
        self.dialogue = DialogueBox(self.font)

        self.toast = ""
        self.toast_timer = 0.0
        self.finished = False
        self.finish_timer = 0.0

    # ---------- events ----------
    def on_quest_completed(self, title, **_):
        self.toast = f"QUEST DONE: {title}"
        self.toast_timer = 3.0

    def nearby_npc(self):
        reach = self.player.rect.inflate(20, 20)
        for npc in self.npcs:
            if reach.colliderect(npc["rect"]):
                return npc
        return None

    def talk(self, npc):
        lines = npc["after_dialogue"] if npc["talked"] else npc["dialogue"]
        first_time = not npc["talked"]
        npc["talked"] = True

        def finish():
            if first_time:
                self.events.emit("npc_talked", npc_id=npc["id"])

        self.dialogue.open(npc["name"], lines, finish)

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
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

    # ---------- update ----------
    def update(self, dt):
        self.dialogue.update(dt)
        if self.toast_timer > 0:
            self.toast_timer -= dt

        if self.finished:
            self.finish_timer -= dt
            if self.finish_timer <= 0:
                self.game.session.complete_stage(self.stage_id)
                self.game.state_manager.pop()
            return

        if self.dialogue.active:
            return  # freeze movement while talking

        self.player.update(dt, self.walls)
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
            self.finish_timer = 2.5
            self.toast = "STAGE COMPLETE!"
            self.toast_timer = 2.5

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
            r = cam.apply(npc["rect"])
            pygame.draw.rect(surface, tuple(npc["color"]), r)
            pygame.draw.rect(surface, (255, 255, 255), r, 1)

        self.player.draw(surface, cam)

        npc = self.nearby_npc()
        if npc and not self.dialogue.active:
            r = cam.apply(npc["rect"])
            tip = self.font.render("E: TALK", False, (255, 255, 120))
            surface.blit(tip, tip.get_rect(midbottom=(r.centerx, r.y - 2)))

        self.draw_quest_hud(surface)
        self.dialogue.draw(surface)

        if self.toast_timer > 0:
            text = self.font.render(self.toast, False, (255, 255, 120))
            bg = text.get_rect(center=(160, 30)).inflate(10, 6)
            pygame.draw.rect(surface, (15, 25, 55), bg)
            pygame.draw.rect(surface, (255, 200, 60), bg, 1)
            surface.blit(text, text.get_rect(center=bg.center))

    def draw_quest_hud(self, surface):
        width, x = 118, settings.INTERNAL_WIDTH - 122
        height = 16 + len(self.quests.quests) * 10
        panel = pygame.Surface((width, height), pygame.SRCALPHA)
        panel.fill((10, 15, 40, 190))
        surface.blit(panel, (x, 4))
        head = f"QUESTS {self.quests.done_count()}/{len(self.quests.quests)}"
        surface.blit(self.font.render(head, False, (255, 200, 60)), (x + 4, 7))
        for i, q in enumerate(self.quests.quests):
            mark = "[x]" if q["done"] else "[ ]"
            color = (110, 230, 130) if q["done"] else (255, 255, 255)
            surface.blit(self.font.render(f"{mark} {q['title']}", False, color), (x + 4, 18 + i * 10))