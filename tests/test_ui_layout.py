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
from src.states.big_map import BigMap
from src.states.character_select import CharacterSelect
from src.states.chapter_intro import ChapterIntro
from src.states.game_over import GameOver
from src.states.guide_state import GuideState
from src.states.high_scores import HighScores
from src.states.loading import LoadingScreen
from src.states.main_menu import MainMenu
from src.states.mission_prep import MissionPrep
from src.states.new_game_confirm import NewGameConfirm
from src.states.options_state import OptionsState
from src.states.stage_complete import StageComplete
from src.states.world_map import WorldMap
from src.ui import theme
from src.ui.choice_box import ChoiceBox
from src.ui.dialogue_box import DialogueBox
from src.utils.data_loader import load_json
from src.utils.helpers import wrap_text


class UILayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT))
        # The game-loop regression test deliberately exercises pygame.quit().
        # Rebuild cached font wrappers if this class runs after that test.
        theme._font_cache.clear()
        cls.surface = pygame.Surface((settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT))
        cls.font = theme.get_font("tiny")

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def assert_queued_text_inside(self, bounds):
        for font, text, _color, (x, y), _shadow in theme.TEXT_QUEUE:
            with self.subTest(text=text):
                # Theme text is rendered after the 4x canvas upscale. Keep a
                # firm lower bound in output pixels so future UI labels cannot
                # silently regress to tiny bitmap lettering.
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

    def assert_queued_text_does_not_collide(self):
        entries = []
        for font, text, _color, (x, y), _shadow in theme.TEXT_QUEUE:
            rect = pygame.Rect(x, y, *font.size(text))
            entries.append((text, rect))
        for index, (text, rect) in enumerate(entries):
            for other_text, other_rect in entries[index + 1:]:
                # A few decorative labels are drawn twice to make pixel fonts
                # bolder. Identical text at the same position is intentional.
                if text == other_text and rect.topleft == other_rect.topleft:
                    continue
                with self.subTest(text=text, other_text=other_text):
                    self.assertFalse(rect.colliderect(other_rect),
                                     f"{text!r} overlaps {other_text!r}")

    def test_all_primary_screens_keep_text_inside_canvas_without_collisions(self):
        root = Path(__file__).resolve().parents[1]
        session = GameSession()
        session.character = json.loads((root / "data" / "characters.json").read_text(
            encoding="utf-8"))[0]
        game = SimpleNamespace(
            session=session,
            state_manager=SimpleNamespace(pop=lambda: None, change=lambda _state: None),
            ask_quit=lambda: None,
            to_canvas_pos=lambda pos: pos,
        )
        stats = {
            "stage_id": "home_island_tutorial", "mission_number": 1,
            "chapter": "Home Village", "lessons": ["Stay safe."],
            "consequences": ["People are safe."], "time": 60, "damage": 0,
            "property_damage": 0, "items_found": 1, "items_total": 2,
            "quests_done": 1, "quests_total": 2, "score": 100,
        }
        menu = MainMenu(game)
        menu.update(0.8)
        character_select = CharacterSelect(game)
        character_select.type_t = 10_000
        guide_state = GuideState(game)
        guide_state.type_t = 1_000_000
        play = BigMap(game, session.current_stage)
        overview = BigMap(game, session.current_stage)
        overview.map_open = True
        places = BigMap(game, session.current_stage)
        places.map_open = True
        places.map_page = "places"
        pause = BigMap(game, session.current_stage)
        pause.paused = True
        dialogue = BigMap(game, session.current_stage)
        dialogue.dialogue.open("KAPITAN JO", ["Move carefully and stay with your group."])
        dialogue.dialogue.chars = 10_000
        choice = BigMap(game, session.current_stage)
        choice.choice.open("KAPITAN JO", "Pick a safe action.", [
            {"text": "Go to the marked safe area."},
            {"text": "Wait near the damaged building."},
        ], lambda _option: None)
        final_stats = {**stats, "stage_id": GameSession.STAGE_ORDER[-1],
                       "mission_number": len(GameSession.STAGE_ORDER),
                       "chapter": "Main Control Room", "ending": "good"}
        screens = (
            menu, character_select, MissionPrep(game, session.current_stage),
            ChapterIntro(game, "home_island_tutorial"),
            LoadingScreen(game, lambda: None), play, overview, places, pause, dialogue,
            choice, guide_state,
            HighScores(game), OptionsState(game), NewGameConfirm(game), WorldMap(game),
            GameOver(game, lambda: None), StageComplete(game, stats),
            StageComplete(game, final_stats),
        )
        canvas = pygame.Rect(0, 0, settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT)
        for screen in screens:
            with self.subTest(screen=type(screen).__name__):
                theme.TEXT_QUEUE.clear()
                screen.draw(self.surface)
                self.assert_queued_text_inside(canvas)
                self.assert_queued_text_does_not_collide()
        theme.TEXT_QUEUE.clear()

    def test_map_places_page_names_every_stop_in_readable_text(self):
        root = Path(__file__).resolve().parents[1]
        session = GameSession()
        session.character = json.loads((root / "data" / "characters.json").read_text(
            encoding="utf-8"))[0]
        game = SimpleNamespace(session=session,
                               state_manager=SimpleNamespace(pop=lambda: None,
                                                             change=lambda _state: None))
        screen = BigMap(game, session.current_stage)
        screen.map_open = True
        screen.map_page = "places"
        theme.TEXT_QUEUE.clear()
        screen.draw(self.surface)
        rendered = {text for _font, text, _color, _pos, _shadow in theme.TEXT_QUEUE}
        for stop_id in screen.route_data["map_places"]:
            self.assertIn(screen.route_data["stops"][stop_id]["label"].upper(), rendered)
        self.assertIn("TAB ROUTE", " ".join(rendered))
        theme.TEXT_QUEUE.clear()

    def test_map_key_opens_and_closes_place_directory(self):
        root = Path(__file__).resolve().parents[1]
        session = GameSession()
        session.character = json.loads((root / "data" / "characters.json").read_text(
            encoding="utf-8"))[0]
        game = SimpleNamespace(session=session,
                               state_manager=SimpleNamespace(pop=lambda: None,
                                                             change=lambda _state: None),
                               to_canvas_pos=lambda pos: pos)
        screen = BigMap(game, session.current_stage)
        screen.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_m))
        self.assertTrue(screen.map_open)
        screen.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_TAB))
        self.assertEqual(screen.map_page, "places")
        screen.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_m))
        self.assertFalse(screen.map_open)

    def test_new_game_enters_preparation_without_forcing_the_route_map_screen(self):
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
        self.assertIsInstance(changed[0].build_next(), MissionPrep)

    def test_character_dialogue_text_stays_in_playfield_safe_bounds(self):
        box = DialogueBox(self.font)
        box.open("KAPITAN JO", ["A long safety instruction " * 12])
        box.chars = 10_000
        box.draw(self.surface, anchor=(319, 23), avoid_rects=(pygame.Rect(160, 0, 160, 22),))
        self.assert_queued_text_inside(pygame.Rect(0, box.BUBBLE_TOP, 320,
                                                  box.BUBBLE_BOTTOM - box.BUBBLE_TOP))
        theme.TEXT_QUEUE.clear()

    def test_all_campaign_npc_lines_fit_the_speech_bubble(self):
        root = Path(__file__).resolve().parents[1]
        for stage_path in sorted((root / "data" / "stages").glob("*.json")):
            stage = json.loads(stage_path.read_text(encoding="utf-8"))
            for npc in stage.get("npcs", []):
                for field in ("dialogue", "after_dialogue", "rescue_dialogue",
                              "rescue_success_dialogue"):
                    for line in npc.get(field, []):
                        with self.subTest(stage=stage_path.stem, npc=npc["name"], field=field):
                            self.assertLessEqual(len(wrap_text(line, self.font, 166)), 5,
                                                 f"line would be cut off: {line!r}")

    def test_choice_card_restores_clip_and_keeps_text_on_canvas(self):
        box = ChoiceBox(self.font)
        box.open("SAFETY CHECK", "Choose the safest response. " * 12,
                 [{"text": "Protect people and move to safe ground. " * 9},
                  {"text": "Wait beside the damaged building. " * 9}], lambda _option: None)
        original_clip = pygame.Rect(0, 0, 320, 180)
        self.surface.set_clip(original_clip)
        box.draw(self.surface)
        self.assertEqual(self.surface.get_clip(), original_clip)
        self.assert_queued_text_inside(original_clip)
        theme.TEXT_QUEUE.clear()

    def test_all_chapter_openers_fit_the_intro_layout(self):
        for stage_id, beat in load_json("data/chapter_openers.json").items():
            with self.subTest(stage=stage_id):
                self.assertLessEqual(self.font.size(beat["chapter"])[0], 300)
                self.assertLessEqual(self.font.size(beat["place"])[0], 300)
                for line in beat["dialogue"]:
                    self.assertLessEqual(len(wrap_text(line["line"], self.font, 245)), 2)
                    self.assertLessEqual(self.font.size(line["speaker"].upper())[0], 245)


if __name__ == "__main__":
    unittest.main()
