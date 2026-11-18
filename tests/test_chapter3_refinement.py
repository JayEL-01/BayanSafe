"""Tests for Chapter 3 Refinement, Mini-games, and Endings."""

import unittest
import pygame
from src.core.game import Game
from src.story.base_level import RadioTuning, TimingMeter, Mash
from src.story.chapter_3.level_3_severe_flooding import Chapter3Level3SevereFlooding
from src.story.chapter_3.level_4_fire_tsunami import Chapter3Level4FireTsunami
from src.story.endings.ending_1_complete_victory import Ending1CompleteVictoryState
from src.story.endings.ending_2_partial_victory import Ending2PartialVictoryState
from src.story.endings.ending_3_total_failure import Ending3TotalFailureState


class TestChapter3Refinement(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((320, 180))

    def setUp(self):
        self.game = Game()
        self.surf = pygame.Surface((320, 180))

    def test_radio_tuning_minigame(self):
        """Test RadioTuning mini-game mechanics and hits/misses."""
        mg = RadioTuning(rounds=2, speed=1.0)
        self.assertEqual(mg.state, "playing")
        # Align pos with target zone center
        mg.pos = mg.zone_c
        self.assertTrue(mg.in_zone())
        mg.press()
        self.assertEqual(mg.hits, 1)
        self.assertEqual(mg.state, "playing")

        # Second hit completes it
        mg.pos = mg.zone_c
        mg.press()
        self.assertEqual(mg.hits, 2)
        self.assertEqual(mg.state, "won")
        # Update timer so finished property resolves
        mg.update(1.0)
        self.assertTrue(mg.finished)

    def test_chapter3_level3_flow(self):
        """Test full Level 3 mechanics: safe decision, breaker, radio, evacuation."""
        lvl = Chapter3Level3SevereFlooding(self.game)

        # Initial state
        self.assertFalse(lvl._rico_assisted)
        self.assertFalse(lvl._breaker_off)
        self.assertFalse(lvl._radio_tuned)

        # Talk to Rico -> starts dialogue and queues decision
        rico = next(n for n in lvl.npcs if n.name == "Rico dela Cruz")
        lvl.on_npc_interacted(rico)
        self.assertIsNotNone(lvl.active_dialogue)

        # Advance through typewriter dialogue lines (two presses per line)
        for _ in range(10):
            if lvl.active_dialogue is None:
                break
            lvl.handle_input("confirm")

        self.assertIsNone(lvl.active_dialogue)

        # Now update opens the queued decision
        lvl.update(0.016)
        self.assertTrue(lvl.decision_system.is_active())

        # Choose unsafe action -> must NOT advance quest, queues retry
        dec = lvl.decision_system.current_decision
        unsafe_idx = next(i for i, opt in enumerate(dec.options) if not opt.get("safe"))
        dec.selected_index = unsafe_idx
        lvl.decision_system.handle_input("confirm")
        self.assertFalse(lvl._rico_assisted)
        self.assertFalse(lvl.completed)

        # Retrying: select safe action
        lvl.update(0.016)
        self.assertTrue(lvl.decision_system.is_active())
        dec = lvl.decision_system.current_decision
        safe_idx = next(i for i, opt in enumerate(dec.options) if opt.get("safe"))
        dec.selected_index = safe_idx
        lvl.decision_system.handle_input("confirm")
        self.assertTrue(lvl._rico_assisted)

        # Breaker mini-game
        lvl._interact_breaker()
        self.assertIsNotNone(lvl.minigame)
        self.assertIsInstance(lvl.minigame, TimingMeter)
        lvl._breaker_success()
        self.assertTrue(lvl._breaker_off)

        # Radio tuning mini-game
        lvl._interact_radio()
        self.assertIsNotNone(lvl.minigame)
        self.assertIsInstance(lvl.minigame, RadioTuning)
        lvl._radio_success()
        self.assertTrue(lvl._radio_tuned)

        # Evacuate to Lighthouse
        lvl.on_trigger_activated("lighthouse_safe")
        self.assertTrue(lvl.completed)

        # Draw frame
        lvl.draw(self.surf)

    def test_chapter3_level4_flow(self):
        """Test full Level 4 mechanics: safe decision, valve shutoff, stairs sprint, evacuation."""
        lvl = Chapter3Level4FireTsunami(self.game)

        # Initial state
        self.assertFalse(lvl._tito_assisted)
        self.assertFalse(lvl._valve_shut)
        self.assertFalse(lvl._stairs_climbed)

        # Talk to Tito Ramon -> starts dialogue and queues decision
        tito = next(n for n in lvl.npcs if n.name == "Tito Ramon")
        lvl.on_npc_interacted(tito)
        self.assertIsNotNone(lvl.active_dialogue)

        # Advance through dialogue
        for _ in range(10):
            if lvl.active_dialogue is None:
                break
            lvl.handle_input("confirm")

        self.assertIsNone(lvl.active_dialogue)

        # Update opens decision
        lvl.update(0.016)
        self.assertTrue(lvl.decision_system.is_active())

        # Unsafe choice -> retries
        dec = lvl.decision_system.current_decision
        unsafe_idx = next(i for i, opt in enumerate(dec.options) if not opt.get("safe"))
        dec.selected_index = unsafe_idx
        lvl.decision_system.handle_input("confirm")
        self.assertFalse(lvl._tito_assisted)

        # Safe choice
        lvl.update(0.016)
        self.assertTrue(lvl.decision_system.is_active())
        dec = lvl.decision_system.current_decision
        safe_idx = next(i for i, opt in enumerate(dec.options) if opt.get("safe"))
        dec.selected_index = safe_idx
        lvl.decision_system.handle_input("confirm")
        self.assertTrue(lvl._tito_assisted)

        # Valve mini-game
        lvl._interact_valve()
        self.assertIsNotNone(lvl.minigame)
        lvl._valve_success()
        self.assertTrue(lvl._valve_shut)
        self.assertTrue(lvl._fire_quenched)

        # Stairs sprint mini-game
        lvl._interact_stairs()
        self.assertIsNotNone(lvl.minigame)
        self.assertIsInstance(lvl.minigame, Mash)
        lvl._stairs_success()
        self.assertTrue(lvl._stairs_climbed)

        # Evacuate to Cliff Lookout
        lvl.on_trigger_activated("cliff_safe")
        self.assertTrue(lvl.completed)

        # Draw frame
        lvl.draw(self.surf)

    def test_endings_multipage(self):
        """Test that all three endings support 3 pages and return to MainMenu."""
        summary = {
            "ending_id": "ending_1_complete_victory",
            "preparedness_ratio": 95,
            "residents_assisted": 8,
            "warnings_followed": 10,
            "unsafe_actions": 0,
        }
        for end_cls in (Ending1CompleteVictoryState, Ending2PartialVictoryState, Ending3TotalFailureState):
            state = end_cls(self.game, summary)
            self.assertEqual(state.page, 0)
            state.draw(self.surf)

            # Advance pages
            state.handle_event(pygame.Event(pygame.KEYDOWN, key=pygame.K_SPACE))
            self.assertEqual(state.page, 1)
            state.draw(self.surf)

            state.handle_event(pygame.Event(pygame.KEYDOWN, key=pygame.K_SPACE))
            self.assertEqual(state.page, 2)
            state.draw(self.surf)

            # Final press returns to MainMenu
            state.handle_event(pygame.Event(pygame.KEYDOWN, key=pygame.K_SPACE))
            from src.states.main_menu import MainMenu
            self.assertIsInstance(self.game.state_manager.current(), MainMenu)


if __name__ == "__main__":
    unittest.main()
