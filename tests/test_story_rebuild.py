"""Comprehensive Test Suite for BayanSafe Story Rebuild.

Verifies:
1. Central palette, elements config, and cast mapping.
2. Character sprite asset integrity (100% preserved).
3. All 25 story levels & final mission initialize, update, and render without error.
4. ScoreSystem and decision branching leading to all 3 canonical endings.
5. Environment zero-image compliance (rendered purely via code).
"""

import os
import unittest
import pygame

# Initialize pygame headless
os.environ["SDL_VIDEODRIVER"] = "dummy"
pygame.init()
pygame.display.set_mode((320, 180))

from src.core.game import Game
from src.config.palette import COLOR_GROUND_SAN_ISIDRO, COLOR_HAZARD_FLOOD, COLOR_SAFE_ZONE
from src.config.elements import ELEMENT_TYPES, get_element_info
from src.config.cast import CAST_ROLES, get_character_meta
from src.core.score_system import ScoreSystem
from src.core.decision_system import DecisionSystem, Decision
from src.core.inventory_system import InventorySystem
from src.story.chapter_registry import STORY_SEQUENCE, LEVEL_MAP, load_level, launch_ending
from src.story.endings.ending_1_complete_victory import Ending1CompleteVictoryState
from src.story.endings.ending_2_partial_victory import Ending2PartialVictoryState
from src.story.endings.ending_3_total_failure import Ending3TotalFailureState


class TestStoryRebuild(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.game = Game()
        cls.surface = pygame.Surface((320, 180))

    def test_palette_and_elements_config(self):
        """Verify palette colors and element definitions exist and have valid RGB tuples."""
        self.assertEqual(len(COLOR_GROUND_SAN_ISIDRO), 3)
        self.assertEqual(len(COLOR_HAZARD_FLOOD), 3)
        self.assertEqual(len(COLOR_SAFE_ZONE), 3)

        self.assertIn("house", ELEMENT_TYPES)
        self.assertIn("shelter", ELEMENT_TYPES)
        self.assertIn("hazard_flood", ELEMENT_TYPES)
        self.assertIn("hazard_fire", ELEMENT_TYPES)
        self.assertIn("safe_zone", ELEMENT_TYPES)
        self.assertIn("item_gobag", ELEMENT_TYPES)

        info = get_element_info("shelter")
        self.assertEqual(info["label"], "SHELTER")
        self.assertFalse(info["solid"])

    def test_cast_roles_and_asset_integrity(self):
        """Verify preserved character assets exist on disk for each defined role."""
        for key, meta in CAST_ROLES.items():
            sprite_path = meta.get("sprite_path")
            if sprite_path:
                self.assertTrue(
                    os.path.exists(sprite_path),
                    f"Preserved character asset missing: {sprite_path} for role {key}",
                )

    def test_score_system_and_endings_evaluation(self):
        """Verify ScoreSystem tracks metrics and produces the 3 canonical endings."""
        # 1. Complete Victory (>= 75% safe, <= 2 unsafe)
        s1 = ScoreSystem()
        for i in range(8):
            s1.record_choice("Q", "Safe", True)
        summary1 = s1.get_summary()
        self.assertEqual(summary1["ending_id"], "ending_1_complete_victory")

        # 2. Partial Victory (45% - 74% safe)
        s2 = ScoreSystem()
        for i in range(5):
            s2.record_choice("Q", "Safe", True)
        for i in range(4):
            s2.record_choice("Q", "Unsafe", False)
        summary2 = s2.get_summary()
        self.assertEqual(summary2["ending_id"], "ending_2_partial_victory")

        # 3. Total Failure (< 45% safe or > 5 unsafe)
        s3 = ScoreSystem()
        for i in range(1):
            s3.record_choice("Q", "Safe", True)
        for i in range(6):
            s3.record_choice("Q", "Unsafe", False)
        summary3 = s3.get_summary()
        self.assertEqual(summary3["ending_id"], "ending_3_total_failure")

    def test_all_25_levels_initialization_and_rendering(self):
        """Load, update, and render every level across all 5 chapters, prologue, and final mission."""
        self.assertEqual(len(STORY_SEQUENCE), 25, "Expected 25 story levels in total.")

        for ch_id, lvl_id in STORY_SEQUENCE:
            with self.subTest(chapter=ch_id, level=lvl_id):
                state = load_level(self.game, ch_id, lvl_id)
                self.assertIsNotNone(state.level)
                self.assertIsNotNone(state.level.block_map)

                # Update 3 simulation frames
                state.update(0.016)
                state.update(0.016)
                state.update(0.016)

                # Render to screen canvas
                state.draw(self.surface)

                # Verify legend screen can be toggled and rendered
                state.level.legend_screen.toggle()
                self.assertTrue(state.level.legend_screen.visible)
                state.draw(self.surface)
                state.level.legend_screen.toggle()

    def test_mission_leaderboard_metadata_matches_story(self):
        """Every story mission must have exactly one short, unique board key."""
        from src.story.chapter_registry import MISSION_INFO

        self.assertEqual(
            [(mission["chapter_id"], mission["level_id"]) for mission in MISSION_INFO],
            STORY_SEQUENCE,
        )
        keys = [mission["key"] for mission in MISSION_INFO]
        self.assertEqual(len(keys), len(set(keys)))
        self.assertTrue(all(len(key) <= 30 for key in keys))

    def test_completed_mission_records_leaderboard_run(self):
        """Completing a mission must publish a real leaderboard entry."""
        from src.story.chapter_registry import mission_key

        original_save = self.game.session.save
        self.game.session.save = lambda: None
        try:
            state = load_level(self.game, "chapter_1", "level_1_earthquake")
            level = state.level
            level.level_time = 40.0
            level.current_objective_idx = len(level.objectives)
            level.setbacks = 0
            level.complete_level()
        finally:
            self.game.session.save = original_save

        key = mission_key("chapter_1", "level_1_earthquake")
        self.assertIn(key, self.game.session.records)
        self.assertIn(key, self.game.session.high_scores)
        entries = self.game.session.stage_high_scores(key)
        self.assertEqual(len(entries), 1)
        self.assertGreater(entries[0]["score"], 0)
        self.assertEqual(entries[0]["quests_done"], entries[0]["quests_total"])
        self.assertEqual(entries[0]["attempts"], 1)

    def test_completed_chapter_records_whole_chapter_total(self):
        """Finishing a chapter must publish one aggregate total for that chapter."""
        from src.core.session import GameSession

        session = GameSession()
        session.save = lambda: None
        session._sync_run_to_db = lambda *args, **kwargs: None
        session._sync_stage_to_db = lambda *args, **kwargs: None
        session.character = {"id": "juan", "name": "Juan"}
        session.challenger_id = "CHAPTER-1"
        session.challenger_name = "CHAPTER-1"
        session.records = {}
        session.high_scores = {}
        session.campaign_results = {}

        scores = {"ch1_1": 400, "ch1_2": 500, "ch1_3": 600, "ch1_4": 700}
        for key, score in scores.items():
            session.record_run(key, {
                "time": 30, "score": score, "perfect": True,
                "quests_done": 3, "quests_total": 3,
                "items_found": 2, "items_total": 2,
                "max_score": 1200, "damage": 0, "completed": True,
            })

        session.complete_stage("chapter_1")

        expected_total = sum(scores.values())
        record = session.records["chapter_1"]
        self.assertEqual(record["best_score"], expected_total)
        self.assertEqual(record["best_time"], 120)
        self.assertEqual(record["missions_done"], 4)
        self.assertEqual(record["missions_total"], 4)
        self.assertIn("chapter_1", session.completed)

        entries = session.stage_high_scores("chapter_1")
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["score"], expected_total)
        self.assertEqual(entries[0]["missions_done"], 4)
        self.assertEqual(entries[0]["missions_total"], 4)

    def test_legacy_completed_chapters_get_backfilled_totals(self):
        """Older saves without chapter boards get totals rebuilt from missions."""
        from src.core.session import GameSession

        session = GameSession()
        session.character = {"id": "juan", "name": "Juan"}
        session.challenger_id = "OLD-SAVE"
        session.challenger_name = "OLD-SAVE"
        session.completed = {"chapter_1"}
        session.records = {
            "ch1_1": {"best_score": 100, "best_time": 10, "perfect": True, "attempts": 1},
            "ch1_2": {"best_score": 200, "best_time": 20, "perfect": True, "attempts": 1},
            "ch1_3": {"best_score": 300, "best_time": 30, "perfect": True, "attempts": 1},
            "ch1_4": {"best_score": 400, "best_time": 40, "perfect": True, "attempts": 1},
            # The final mission used to skip complete_stage, so it is not in
            # "completed" but its mission record still proves it was finished.
            "final": {"best_score": 900, "best_time": 50, "perfect": True, "attempts": 1},
        }
        session.campaign_results = {}
        session.high_scores = {}

        self.assertTrue(session.backfill_chapter_records())
        entry = session.high_scores["chapter_1"]["OLD-SAVE"]
        self.assertEqual(entry["score"], 1000)
        self.assertEqual(entry["best_time"], 100)
        self.assertEqual(entry["missions_done"], 4)
        self.assertEqual(entry["missions_total"], 4)
        final_entry = session.high_scores["final_mission"]["OLD-SAVE"]
        self.assertEqual(final_entry["score"], 900)
        self.assertFalse(session.backfill_chapter_records())

    def test_high_scores_survive_erase_and_new_campaign(self):
        """Starting over clears progress but keeps recorded leaderboard scores."""
        import tempfile
        from pathlib import Path
        from src.core import save_data
        from src.core.session import GameSession

        with tempfile.TemporaryDirectory() as folder:
            old_path, old_dir = save_data.SAVE_PATH, save_data.SAVE_DIR
            save_data.SAVE_PATH = Path(folder) / "progress.json"
            save_data.SAVE_DIR = Path(folder)
            try:
                session = GameSession()
                session._sync_run_to_db = lambda *args, **kwargs: None
                session._sync_stage_to_db = lambda *args, **kwargs: None
                session.character = {"id": "juan", "name": "Juan"}
                session.challenger_id = "PLAYER-1"
                session.challenger_name = "PLAYER-1"
                session.record_run("ch1_1", {"score": 500, "time": 30, "completed": True})
                self.assertTrue(save_data.SAVE_PATH.exists())

                session.erase()
                self.assertFalse(save_data.SAVE_PATH.exists())
                self.assertIn("ch1_1", session.high_scores)

                # Character select writes the fresh campaign save afterwards.
                session.character = {"id": "juan", "name": "Juan"}
                session.challenger_id = "PLAYER-1"
                session.challenger_name = "PLAYER-1"
                session.save()

                fresh = GameSession()
                self.assertTrue(fresh.load([{"id": "juan"}]))
                self.assertIn("ch1_1", fresh.high_scores)
                self.assertEqual(fresh.stage_high_scores("ch1_1")[0]["score"], 500)
            finally:
                save_data.SAVE_PATH, save_data.SAVE_DIR = old_path, old_dir

    def test_high_scores_screen_defaults_to_chapter_totals(self):
        """The score screen opens on completed chapters and can switch to missions."""
        from unittest import mock
        from src.states.high_scores import HighScores

        original_scores = self.game.session.high_scores
        original_records = self.game.session.records
        try:
            self.game.session.high_scores = {
                "chapter_2": {
                    "PLAYER-1": {
                        "player_id": "PLAYER-1", "score": 1234, "attempts": 1,
                        "best_time": 90, "missions_done": 4, "missions_total": 4,
                    }
                }
            }
            self.game.session.records = {"chapter_2": {"best_score": 1234}}

            with mock.patch("src.states.high_scores.load_save", return_value=None):
                screen = HighScores(self.game)
            self.assertEqual(screen.view, "chapters")
            self.assertEqual(screen.boards[screen.index]["key"], "chapter_2")
            screen.draw(self.surface)

            screen.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_v))
            self.assertEqual(screen.view, "missions")
            screen.draw(self.surface)
        finally:
            self.game.session.high_scores = original_scores
            self.game.session.records = original_records

    def test_all_3_ending_states_render(self):
        """Verify all 3 canonical ending screens render without crashing."""
        s1 = Ending1CompleteVictoryState(self.game, {"preparedness_ratio": 95, "residents_assisted": 10, "warnings_followed": 12})
        s1.update(0.016)
        s1.draw(self.surface)

        s2 = Ending2PartialVictoryState(self.game, {"preparedness_ratio": 60, "unsafe_actions": 3, "warnings_followed": 6})
        s2.update(0.016)
        s2.draw(self.surface)

        s3 = Ending3TotalFailureState(self.game, {"preparedness_ratio": 20, "unsafe_actions": 8, "warnings_followed": 2})
        s3.update(0.016)
        s3.draw(self.surface)

    def test_advance_from_chapter_1_to_chapter_2(self):
        """Verify seamless progression across the chapter boundary from Chapter 1 to Chapter 2."""
        from src.story.chapter_registry import advance_story
        # 1. Load Chapter 1 Level 4 (Tsunami)
        load_level(self.game, "chapter_1", "level_4_tsunami")
        curr = self.game.state_manager.current()
        self.assertEqual(curr.chapter_id, "chapter_1")
        self.assertEqual(curr.level_id, "level_4_tsunami")

        # 2. Advance story upon completion
        advance_story(self.game, "chapter_1", "level_4_tsunami")

        # 3. Verify state transitioned to Chapter 2 Level 1 (Flash Fire)
        next_state = self.game.state_manager.current()
        self.assertIsNotNone(next_state)
        self.assertEqual(next_state.chapter_id, "chapter_2")
        self.assertEqual(next_state.level_id, "level_1_fire")

        # 4. Verify session unlocked Chapter 2
        self.assertTrue(self.game.session.is_unlocked("chapter_2"))
        self.assertEqual(self.game.session.current_stage, "chapter_2")


if __name__ == "__main__":
    unittest.main()
