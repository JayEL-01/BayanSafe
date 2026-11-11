"""Regression checks for readable, bounded in-game overlays."""
import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import unittest
import json
from pathlib import Path
from types import SimpleNamespace

import pygame

from src.core import settings
from src.core.session import GameSession
from src.states.chapter import ChapterState
from src.states.character_select import CharacterSelect
from src.states.game_over import GameOver
from src.states.guide_state import GuideState
from src.states.high_scores import HighScores
from src.states.loading import LoadingScreen
from src.states.main_menu import MainMenu
from src.states.new_game_confirm import NewGameConfirm
from src.states.options_state import OptionsState
from src.states.stage_complete import StageComplete
from src.states.world_map import WorldMap
from src.ui import theme
from src.ui.choice_box import ChoiceBox
from src.ui.dialogue_box import DialogueBox
from src.utils.helpers import wrap_text


class UILayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT))
        theme._font_cache.clear()
        cls.surface = pygame.Surface((settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT))
        cls.font = theme.get_font("tiny")

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def assert_queued_text_inside(self, bounds):
        for font, text, _color, (x, y), _shadow in theme.TEXT_QUEUE:
            with self.subTest(text=text):
                self.assertGreaterEqual(font.font.get_height(), 28)
                glyphs = font.font.metrics(text)
                missing = [char for char, metric in zip(text, glyphs)
                           if not char.isspace() and metric is None]
                self.assertEqual(missing, [], f"unsupported glyphs in {text!r}")
                width, height = font.size(text)
                self.assertGreaterEqual(x, bounds.left)
                self.assertGreaterEqual(y, bounds.top)
                self.assertLessEqual(x + width, bounds.right)
                self.assertLessEqual(y + height, bounds.bottom)

    def test_all_primary_screens_keep_text_inside_canvas(self):
        root = Path(__file__).resolve().parents[1]
        session = GameSession()
        session.character = json.loads((root / "data" / "characters.json").read_text(
            encoding="utf-8"))[0]
        game = SimpleNamespace(
            session=session,
            state_manager=SimpleNamespace(pop=lambda: None, change=lambda _state: None, push=lambda _state: None),
            ask_quit=lambda: None,
            to_canvas_pos=lambda pos: pos,
        )

        menu = MainMenu(game)
        menu.update(0.8)
        character_select = CharacterSelect(game)
        guide_state = GuideState(game)
        world_map = WorldMap(game)
        play = ChapterState(game, "prologue")
        pause = ChapterState(game, "prologue")
        pause.paused = True
        dialogue = ChapterState(game, "prologue")
        dialogue.dialogue.open("KAP. BEN", ["Move carefully and stay with your group."])
        dialogue.dialogue.chars = 10_000
        choice = ChapterState(game, "prologue")
        choice.choice.open("KAP. BEN", "Pick a safe action.", [
            {"text": "Go to the marked safe area."},
            {"text": "Wait near the building."},
        ], lambda _option: None)

        screens = (
            menu, character_select, world_map,
            LoadingScreen(game, lambda: None), play, pause, dialogue,
            choice, guide_state,
            HighScores(game), OptionsState(game), NewGameConfirm(game),
            GameOver(game, lambda: None), StageComplete(game),
        )
        canvas = pygame.Rect(0, 0, settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT)
        for screen in screens:
            with self.subTest(screen=type(screen).__name__):
                theme.TEXT_QUEUE.clear()
                screen.draw(self.surface)
                self.assert_queued_text_inside(canvas)
        theme.TEXT_QUEUE.clear()

    def test_new_game_transitions_to_world_map(self):
        root = Path(__file__).resolve().parents[1]
        session = GameSession()
        session.character = json.loads((root / "data" / "characters.json").read_text(
            encoding="utf-8"))[0]
        session.save = lambda: None
        changed = []
        game = SimpleNamespace(session=session,
                               state_manager=SimpleNamespace(change=changed.append))
        CharacterSelect(game)._finish()
        self.assertEqual(len(changed), 1)
        self.assertIsInstance(changed[0], LoadingScreen)
        next_state = changed[0].build_next()
        self.assertIsInstance(next_state, WorldMap)

    def test_character_dialogue_text_stays_in_playfield_safe_bounds(self):
        box = DialogueBox(self.font)
        box.open("KAP. BEN", ["A safety instruction for all neighbors."])
        box.chars = 10_000
        box.draw(self.surface, anchor=(319, 23), avoid_rects=(pygame.Rect(160, 0, 160, 22),))
        self.assert_queued_text_inside(pygame.Rect(0, box.BUBBLE_TOP, 320,
                                                  box.BUBBLE_BOTTOM - box.BUBBLE_TOP))
        theme.TEXT_QUEUE.clear()

    def test_all_story_npc_lines_fit_speech_bubble(self):
        root = Path(__file__).resolve().parents[1]
        for story_path in sorted((root / "data" / "story").glob("*.json")):
            story = json.loads(story_path.read_text(encoding="utf-8"))
            for npc in story.get("npcs", []):
                for line in npc.get("dialogue", []):
                    with self.subTest(story=story_path.stem, npc=npc.get("name", "NPC")):
                        self.assertLessEqual(len(wrap_text(line, self.font, 166)), 5,
                                             f"line would be cut off: {line!r}")

    def test_choice_card_restores_clip_and_keeps_text_on_canvas(self):
        box = ChoiceBox(self.font)
        box.open("SAFETY CHECK", "Choose the safest response.",
                 [{"text": "Protect people and move to safe ground."},
                  {"text": "Wait beside the building."}], lambda _option: None)
        original_clip = pygame.Rect(0, 0, 320, 180)
        self.surface.set_clip(original_clip)
        box.draw(self.surface)
        self.assertEqual(self.surface.get_clip(), original_clip)
        self.assert_queued_text_inside(original_clip)
        theme.TEXT_QUEUE.clear()


if __name__ == "__main__":
    unittest.main()
