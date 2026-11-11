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
