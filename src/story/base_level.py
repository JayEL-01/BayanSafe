"""Base Level Framework for BayanSafe Story Chapters.

Coordinates the code-rendered BlockMap, animated NPC sprites, Player entity,
active environmental Hazards, Decision prompts, and HUD rendering with zero
environment image dependencies.
"""

from typing import List, Dict, Any, Optional
import pygame

from src.core import settings
from src.world.camera import Camera
from src.entities.player import Player
from src.entities.npc import NPC
from src.maps.block_map import BlockMap
from src.hazards.base_hazard import BaseHazard
from src.core.decision_system import DecisionSystem, Decision
from src.core.score_system import ScoreSystem
from src.ui.legend_screen import LegendScreen
from src.ui.pause_menu import PauseMenu
from src.ui import theme
from src.config.palette import (
    COLOR_UI_PANEL,
    COLOR_UI_BORDER,
    COLOR_UI_TEXT,
    COLOR_UI_ACCENT,
    COLOR_UI_DANGER,
    COLOR_UI_SAFE,
)


class BaseLevel:
    def __init__(
        self,
        game,
        chapter_id: str,
        level_id: str,
        title: str,
        subtitle: str,
        disaster_type: str,
        lesson_source: str,
        lesson_text: str,
    ):
        self.game = game
        self.chapter_id = chapter_id
        self.level_id = level_id
        self.title = title
        self.subtitle = subtitle
        self.disaster_type = disaster_type
        self.lesson_source = lesson_source
        self.lesson_text = lesson_text

        # Ensure session has score system
        if not hasattr(self.game.session, "score_system"):
            self.game.session.score_system = ScoreSystem()
        self.score_system: ScoreSystem = self.game.session.score_system

        # Core systems
        self.decision_system = DecisionSystem(self.score_system)
        self.legend_screen = LegendScreen()
        self.pause_menu = PauseMenu(self.game)

        # Map & Camera (child level sets up self.block_map)
        self.block_map: Optional[BlockMap] = None
        self.camera = Camera(640, 360)

        # Entities
        char_choice = getattr(self.game.session, "character", "juan")
        walk_path = f"assets/images/characters/{char_choice}_walk.png"
        self.player = Player(100, 100, speed=80, walk_path=walk_path)
        self.npcs: List[NPC] = []
        self.hazards: List[BaseHazard] = []

        # Objective tracking
        self.objectives: List[str] = []
        self.current_objective_idx: int = 0
        self.completed: bool = False
        self.show_lesson_modal: bool = False

        # Active dialogue state
        self.active_dialogue: Optional[List[str]] = None
        self.dialogue_speaker: str = ""
        self.dialogue_idx: int = 0

    def add_npc(self, char_id: str, name: str, pos: tuple, dialogue: List[str], role: str = ""):
        """Add an NPC with preserved character art walk-sheet."""
        npc_data = {
            "id": char_id,
            "name": name,
            "pos": pos,
            "color": (220, 180, 100),
            "dialogue": dialogue,
        }
        npc = NPC(npc_data)
        self.npcs.append(npc)
        return npc

    def handle_input(self, action: str) -> bool:
        """Process keyboard / game input."""
        # 1. Legend screen takes input if open
        if self.legend_screen.visible:
            return self.legend_screen.handle_input(action)

        if action == "legend":
            self.legend_screen.toggle()
            return True

        # 2. Stage completion lesson modal
        if self.show_lesson_modal:
            if action in ("confirm", "interact", "cancel", "escape"):
                self.proceed_to_next()
                return True
            return True

        # 3. Pause menu
        if self.pause_menu.visible:
            return self.pause_menu.handle_input(action, level=self)

        # 4. Escape / Pause key during normal gameplay
        if action in ("escape", "pause"):
            if self.active_dialogue is not None:
                # Close dialogue if talking
                self.active_dialogue = None
                self.dialogue_speaker = ""
                return True
            self.pause_menu.show()
            return True

        # 5. Decision system takes input if active
        if self.decision_system.is_active():
            return self.decision_system.handle_input(action)

        # 6. Dialogue progression
        if self.active_dialogue is not None:
            if action in ("confirm", "interact", "space"):
                self.dialogue_idx += 1
                if self.dialogue_idx >= len(self.active_dialogue):
                    self.active_dialogue = None
                    self.dialogue_speaker = ""
                return True
            return True

        # 7. World interaction
        if action in ("confirm", "interact"):
            return self._try_interact()

        return False

    def _try_interact(self) -> bool:
        p_center = self.player.rect.center
        for npc in self.npcs:
            dx = npc.rect.centerx - p_center[0]
            dy = npc.rect.centery - p_center[1]
            if (dx * dx + dy * dy) <= (28 * 28):
                self.start_dialogue(npc.name, npc.dialogue)
                self.on_npc_interacted(npc)
                return True
        return False

    def on_npc_interacted(self, npc: NPC):
        pass

    def start_dialogue(self, speaker: str, lines: List[str]):
        self.dialogue_speaker = speaker
        self.active_dialogue = lines
        self.dialogue_idx = 0

    def trigger_decision(self, decision: Decision):
        self.decision_system.trigger_decision(decision)

    def complete_objective(self):
        self.current_objective_idx += 1
        if self.current_objective_idx >= len(self.objectives):
            self.complete_level()

    def complete_level(self):
        self.completed = True
        self.show_lesson_modal = True

    def proceed_to_next(self):
        from src.story.chapter_registry import advance_story
        advance_story(self.game, self.chapter_id, self.level_id)

    def update(self, dt: float):
        if self.legend_screen.visible or self.show_lesson_modal or self.pause_menu.visible:
            return

        self.decision_system.update(dt)

        # Player movement
        if not self.decision_system.is_active() and self.active_dialogue is None:
            wind_push = pygame.Vector2(0, 0)
            for h in self.hazards:
                if hasattr(h, "get_wind_push"):
                    wind_push += h.get_wind_push()

            walls = self.block_map.collision_rects if self.block_map else []
            self.player.update(dt, walls=walls, push=wind_push)

            # Check item pickups
            if self.block_map:
                picked = self.block_map.check_item_pickup(self.player.rect)
                if picked:
                    if hasattr(self.game.session, "inventory"):
                        self.game.session.inventory.add_item(picked.item_id)
                    self.on_item_collected(picked.item_id)

            # Check triggers with generous collision bounds for safe zones / high ground
            if self.block_map:
                triggers = self.block_map.check_triggers(self.player.rect.inflate(12, 12))
                for tr in triggers:
                    self.on_trigger_activated(tr)

        # Update hazards
        for h in self.hazards:
            h.update(dt, self.player.pos, self.block_map)

        # Update NPCs
        for npc in self.npcs:
            if hasattr(npc, "update"):
                npc.update(dt, self.block_map.collision_rects if self.block_map else [])

        # Update block map animations
        if self.block_map:
            self.block_map.update(dt)

        # Update camera follow
        self.camera.follow(self.player.rect)

    def on_item_collected(self, item_id: str):
        pass

    def on_trigger_activated(self, trigger_id: str):
        pass

    def draw(self, surface: pygame.Surface):
        shake_offset = (0, 0)
        for h in self.hazards:
            sx, sy = h.get_screen_shake()
            if sx != 0 or sy != 0:
                shake_offset = (sx, sy)
                break

        world_surf = surface
        if shake_offset != (0, 0):
            world_surf = surface.copy()

        # 1. Draw Code-Rendered BlockMap
        if self.block_map:
            self.block_map.draw(world_surf, self.camera)

        # 2. Draw NPCs (preserved character art)
        for npc in self.npcs:
            if hasattr(npc, "draw"):
                npc.draw(world_surf, self.camera)
            else:
                s_rect = self.camera.apply(npc.rect)
                pygame.draw.rect(world_surf, (220, 180, 100), s_rect)

            s_rect = self.camera.apply(npc.rect)
            if 20 <= s_rect.centerx <= 300 and 12 <= s_rect.top <= 168:
                theme.draw_text(
                    world_surf,
                    npc.name,
                    (s_rect.centerx, s_rect.top - 8),
                    size="tiny",
                    color=COLOR_UI_TEXT,
                    shadow=True,
                    anchor="center",
                )

        # 3. Draw Player (preserved character art)
        if hasattr(self.player, "draw"):
            self.player.draw(world_surf, self.camera)
        else:
            p_screen = self.camera.apply(self.player.rect)
            pygame.draw.rect(world_surf, (255, 200, 60), p_screen)

        # 4. Draw Hazard Visual Effects
        for h in self.hazards:
            h.draw_effects(world_surf, self.camera)

        if shake_offset != (0, 0):
            surface.blit(world_surf, shake_offset)

        # 5. Draw HUD
        self._draw_hud(surface)

        # 6. Dialogue Box
        if self.active_dialogue is not None and self.dialogue_idx < len(self.active_dialogue):
            self._draw_dialogue_box(surface)

        # 7. Decision Box
        if self.decision_system.is_active():
            self._draw_decision_box(surface)

        # 8. Lesson Modal
        if self.show_lesson_modal:
            self._draw_lesson_modal(surface)

        # 9. Legend Screen
        if self.legend_screen.visible:
            self.legend_screen.draw(surface)

        # 10. Pause Menu
        if self.pause_menu.visible:
            self.pause_menu.draw(surface)

    def _draw_hud(self, surface: pygame.Surface):
        w, h = surface.get_size()
        pygame.draw.rect(surface, (20, 24, 28), (0, 0, w, 14))
        pygame.draw.line(surface, COLOR_UI_BORDER, (0, 14), (w, 14), 1)

        theme.draw_text(
            surface,
            f"DISASTER STATUS: {self.disaster_type.upper()}",
            (8, 2),
            size="tiny",
            color=COLOR_UI_DANGER,
            shadow=False,
            anchor="topleft",
        )

        theme.draw_text(
            surface,
            "[ESC] Pause | [L] Legend | [SPACE] Interact",
            (w - 8, 2),
            size="tiny",
            color=COLOR_UI_ACCENT,
            shadow=False,
            anchor="topright",
        )

        obj_text = (
            self.objectives[self.current_objective_idx]
            if self.current_objective_idx < len(self.objectives)
            else "Evacuation Objective Complete"
        )
        obj_w = min(w - 16, 220)
        pygame.draw.rect(surface, COLOR_UI_PANEL, (8, 18, obj_w, 16))
        pygame.draw.rect(surface, COLOR_UI_BORDER, (8, 18, obj_w, 16), 1)

        theme.draw_text(
            surface,
            f"OBJ: {obj_text}",
            (12, 22),
            size="tiny",
            color=COLOR_UI_TEXT,
            shadow=False,
            anchor="topleft",
        )

    def _draw_dialogue_box(self, surface: pygame.Surface):
        w, h = surface.get_size()
        box_w = w - 24
        box_h = 42
        box_x = 12
        box_y = h - box_h - 10

        pygame.draw.rect(surface, COLOR_UI_PANEL, (box_x, box_y, box_w, box_h))
        pygame.draw.rect(surface, COLOR_UI_BORDER, (box_x, box_y, box_w, box_h), 2)

        theme.draw_text(
            surface,
            self.dialogue_speaker.upper(),
            (box_x + 8, box_y + 4),
            size="tiny",
            color=COLOR_UI_ACCENT,
            shadow=True,
            anchor="topleft",
        )

        current_line = self.active_dialogue[self.dialogue_idx]
        theme.draw_text(
            surface,
            current_line,
            (box_x + 8, box_y + 16),
            size="tiny",
            color=COLOR_UI_TEXT,
            shadow=False,
            anchor="topleft",
        )

        theme.draw_text(
            surface,
            "[SPACE] Continue",
            (box_x + box_w - 6, box_y + box_h - 10),
            size="tiny",
            color=COLOR_UI_ACCENT,
            shadow=False,
            anchor="topright",
        )

    def _draw_decision_box(self, surface: pygame.Surface):
        dec = self.decision_system.current_decision
        if not dec:
            return
        w, h = surface.get_size()
        box_w = min(w - 24, 280)
        box_h = 76
        box_x = (w - box_w) // 2
        box_y = (h - box_h) // 2

        pygame.draw.rect(surface, COLOR_UI_PANEL, (box_x, box_y, box_w, box_h))
        pygame.draw.rect(surface, COLOR_UI_DANGER, (box_x, box_y, box_w, box_h), 2)

        theme.draw_text(
            surface,
            "CRITICAL PREPAREDNESS DECISION",
            (w // 2, box_y + 5),
            size="tiny",
            color=COLOR_UI_ACCENT,
            shadow=True,
            anchor="center",
        )

        theme.draw_text(
            surface,
            dec.prompt,
            (box_x + 8, box_y + 18),
            size="tiny",
            color=COLOR_UI_TEXT,
            shadow=False,
            anchor="topleft",
        )

        for idx, opt in enumerate(dec.options):
            opt_y = box_y + 34 + idx * 14
            is_sel = idx == dec.selected_index
            color = COLOR_UI_ACCENT if is_sel else COLOR_UI_TEXT
            prefix = "> " if is_sel else "  "
            theme.draw_text(
                surface,
                f"{prefix}{opt['text']}",
                (box_x + 8, opt_y),
                size="tiny",
                color=color,
                shadow=False,
                anchor="topleft",
            )

        theme.draw_text(
            surface,
            "[UP/DOWN] Select  |  [SPACE] Confirm",
            (w // 2, box_y + box_h - 10),
            size="tiny",
            color=COLOR_UI_ACCENT,
            shadow=False,
            anchor="center",
        )

    def _draw_lesson_modal(self, surface: pygame.Surface):
        w, h = surface.get_size()
        overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        overlay.fill((10, 15, 20, 230))
        surface.blit(overlay, (0, 0))

        box_w = min(w - 24, 290)
        box_h = 130
        box_x = (w - box_w) // 2
        box_y = (h - box_h) // 2

        pygame.draw.rect(surface, COLOR_UI_PANEL, (box_x, box_y, box_w, box_h))
        pygame.draw.rect(surface, COLOR_UI_SAFE, (box_x, box_y, box_w, box_h), 2)

        theme.draw_text(
            surface,
            "STAGE COMPLETED - DISASTER LESSON",
            (w // 2, box_y + 6),
            size="small",
            color=COLOR_UI_SAFE,
            shadow=True,
            anchor="center",
        )

        theme.draw_text(
            surface,
            f"SOURCE: {self.lesson_source}",
            (box_x + 10, box_y + 24),
            size="tiny",
            color=COLOR_UI_ACCENT,
            shadow=False,
            anchor="topleft",
        )

        lines = self.lesson_text.split("\n")
        curr_y = box_y + 38
        for line in lines[:5]:
            theme.draw_text(
                surface,
                line.strip(),
                (box_x + 10, curr_y),
                size="tiny",
                color=COLOR_UI_TEXT,
                shadow=False,
                anchor="topleft",
            )
            curr_y += 11

        theme.draw_text(
            surface,
            "[SPACE] / [ENTER] Continue Journey",
            (w // 2, box_y + box_h - 12),
            size="tiny",
            color=COLOR_UI_ACCENT,
            shadow=True,
            anchor="center",
        )
