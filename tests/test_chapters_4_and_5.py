"""Tests for Chapter 4, Chapter 5, Final Mission, and Enhanced Chapter Endings."""

import unittest
import pygame
from src.core.game import Game
from src.story.chapter_4.level_1_typhoon import Chapter4Level1Typhoon
from src.story.chapter_4.level_2_flash_flood import Chapter4Level2FlashFlood
from src.story.chapter_4.level_3_landslide import Chapter4Level3Landslide
from src.story.chapter_4.level_4_earthquake_volcano import Chapter4Level4EarthquakeVolcano
from src.story.chapter_5.level_1_earthquake_landslide import Chapter5Level1EarthquakeLandslide
from src.story.chapter_5.level_2_volcano import Chapter5Level2Volcano
from src.story.chapter_5.level_3_flash_fire import Chapter5Level3FlashFire
from src.story.chapter_5.level_4_typhoon_severe_flood import Chapter5Level4TyphoonSevereFlood
from src.story.final_mission.shutdown_machine import FinalMissionShutdownMachine
from src.story.chapter_registry import StoryTransitionState, advance_story, launch_ending, CHAPTER_RECAPS


class TestChapters4And5(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((320, 180))

    def setUp(self):
        self.game = Game()
        self.surf = pygame.Surface((320, 180))

    def test_chapter_4_level_1(self):
        """Test Chapter 4 Level 1 flow."""
        lvl = Chapter4Level1Typhoon(self.game)
        jun = next(n for n in lvl.npcs if n.name == "Jun")
        lvl.on_npc_interacted(jun)
        for _ in range(8):
            if lvl.active_dialogue is None:
                break
            lvl.handle_input("confirm")
        lvl.update(0.016)
        self.assertTrue(lvl.decision_system.is_active())

        # Safe decision
        dec = lvl.decision_system.current_decision
        dec.selected_index = next(i for i, o in enumerate(dec.options) if o.get("safe"))
        lvl.decision_system.handle_input("confirm")
        self.assertTrue(lvl._jun_assisted)

        # Mini-games
        lvl._interact_corral()
        lvl._corral_success()
        self.assertTrue(lvl._livestock_freed)

        lvl._interact_dike()
        lvl._dike_success()
        self.assertTrue(lvl._dike_reinforced)

        lvl.on_trigger_activated("silo_safe")
        self.assertTrue(lvl.completed)
        lvl.draw(self.surf)

    def test_chapter_4_level_2(self):
        """Test Chapter 4 Level 2 flow."""
        lvl = Chapter4Level2FlashFlood(self.game)
        rosa = next(n for n in lvl.npcs if n.name == "Aling Rosa")
        lvl.on_npc_interacted(rosa)
        for _ in range(8):
            if lvl.active_dialogue is None:
                break
            lvl.handle_input("confirm")
        lvl.update(0.016)
        self.assertTrue(lvl.decision_system.is_active())

        dec = lvl.decision_system.current_decision
        dec.selected_index = next(i for i, o in enumerate(dec.options) if o.get("safe"))
        lvl.decision_system.handle_input("confirm")
        self.assertTrue(lvl._rosa_assisted)

        lvl._interact_probe()
        lvl._probe_success()
        self.assertTrue(lvl._road_probed)

        lvl._interact_harvest()
        lvl._harvest_success()
        self.assertTrue(lvl._harvest_saved)

        lvl.on_trigger_activated("terminal_safe")
        self.assertTrue(lvl.completed)
        lvl.draw(self.surf)

    def test_chapter_4_level_3(self):
        """Test Chapter 4 Level 3 flow."""
        lvl = Chapter4Level3Landslide(self.game)
        lvl._interact_scree()
        lvl.minigame = None
        lvl._scree_success()
        self.assertTrue(lvl._scree_crossed)

        lvl._interact_conduit()
        lvl.minigame = None
        lvl._conduit_success()
        self.assertTrue(lvl._telemetry_decoded)

        reyes = next(n for n in lvl.npcs if n.name == "Dr. Elena Reyes")
        lvl.on_npc_interacted(reyes)
        for _ in range(8):
            if lvl.active_dialogue is None:
                break
            lvl.handle_input("confirm")
        lvl.update(0.016)
        self.assertTrue(lvl.decision_system.is_active())

        dec = lvl.decision_system.current_decision
        dec.selected_index = next(i for i, o in enumerate(dec.options) if o.get("safe"))
        lvl.decision_system.handle_input("confirm")
        self.assertTrue(lvl._reyes_assisted)

        lvl.on_trigger_activated("seismo_safe")
        self.assertTrue(lvl.completed)
        lvl.draw(self.surf)

    def test_chapter_4_level_4(self):
        """Test Chapter 4 Level 4 flow."""
        lvl = Chapter4Level4EarthquakeVolcano(self.game)
        santos = next(n for n in lvl.npcs if n.name == "Dr. Mira Santos")
        lvl.on_npc_interacted(santos)
        for _ in range(8):
            if lvl.active_dialogue is None:
                break
            lvl.handle_input("confirm")
        lvl.update(0.016)
        self.assertTrue(lvl.decision_system.is_active())

        dec = lvl.decision_system.current_decision
        dec.selected_index = next(i for i, o in enumerate(dec.options) if o.get("safe"))
        lvl.decision_system.handle_input("confirm")
        self.assertTrue(lvl._santos_assisted)

        lvl._interact_sensor()
        lvl._sensor_success()
        self.assertTrue(lvl._sensor_calibrated)

        lvl._interact_gate()
        lvl._gate_success()
        self.assertTrue(lvl._gate_locked)

        lvl.on_trigger_activated("pdz_safe")
        self.assertTrue(lvl.completed)
        lvl.draw(self.surf)

    def test_chapter_5_level_1(self):
        """Test Chapter 5 Level 1 flow."""
        lvl = Chapter5Level1EarthquakeLandslide(self.game)
        paolo = next(n for n in lvl.npcs if n.name == "Engr. Paolo Santos")
        lvl.on_npc_interacted(paolo)
        for _ in range(8):
            if lvl.active_dialogue is None:
                break
            lvl.handle_input("confirm")
        lvl.update(0.016)
        self.assertTrue(lvl.decision_system.is_active())

        dec = lvl.decision_system.current_decision
        dec.selected_index = next(i for i, o in enumerate(dec.options) if o.get("safe"))
        lvl.decision_system.handle_input("confirm")
        self.assertTrue(lvl._paolo_assisted)

        lvl._interact_boulder()
        lvl._boulder_success()
        self.assertTrue(lvl._boulder_cleared)

        lvl._interact_fissure()
        lvl._fissure_success()
        self.assertTrue(lvl._fissure_crossed)

        lvl.on_trigger_activated("gate_safe")
        self.assertTrue(lvl.completed)
        lvl.draw(self.surf)

    def test_chapter_5_level_2(self):
        """Test Chapter 5 Level 2 flow."""
        lvl = Chapter5Level2Volcano(self.game)
        rhea = next(n for n in lvl.npcs if n.name == "Rhea")
        lvl.on_npc_interacted(rhea)
        for _ in range(8):
            if lvl.active_dialogue is None:
                break
            lvl.handle_input("confirm")
        lvl.update(0.016)
        self.assertTrue(lvl.decision_system.is_active())

        dec = lvl.decision_system.current_decision
        dec.selected_index = next(i for i, o in enumerate(dec.options) if o.get("safe"))
        lvl.decision_system.handle_input("confirm")
        self.assertTrue(lvl._rhea_assisted)

        lvl._interact_mask()
        lvl._mask_success()
        self.assertTrue(lvl._mask_fitted)

        lvl._interact_bus()
        lvl._bus_success()
        self.assertTrue(lvl._bus_cleared)

        lvl.on_trigger_activated("convoy_safe")
        self.assertTrue(lvl.completed)
        lvl.draw(self.surf)

    def test_chapter_5_level_3(self):
        """Test Chapter 5 Level 3 flow."""
        lvl = Chapter5Level3FlashFire(self.game)
        paolo = next(n for n in lvl.npcs if n.name == "Engr. Paolo Santos")
        lvl.on_npc_interacted(paolo)
        for _ in range(8):
            if lvl.active_dialogue is None:
                break
            lvl.handle_input("confirm")
        lvl.update(0.016)
        self.assertTrue(lvl.decision_system.is_active())

        dec = lvl.decision_system.current_decision
        dec.selected_index = next(i for i, o in enumerate(dec.options) if o.get("safe"))
        lvl.decision_system.handle_input("confirm")
        self.assertTrue(lvl._paolo_assisted)

        lvl._interact_firebreak()
        lvl._firebreak_success()
        self.assertTrue(lvl._firebreak_dug)

        lvl._interact_airlock()
        lvl._airlock_success()
        self.assertTrue(lvl._airlock_unsealed)

        lvl.on_trigger_activated("airlock_safe")
        self.assertTrue(lvl.completed)
        lvl.draw(self.surf)

    def test_chapter_5_level_4(self):
        """Test Chapter 5 Level 4 flow."""
        lvl = Chapter5Level4TyphoonSevereFlood(self.game)
        mayor = next(n for n in lvl.npcs if n.name == "Mayor Cruz")
        lvl.on_npc_interacted(mayor)
        for _ in range(8):
            if lvl.active_dialogue is None:
                break
            lvl.handle_input("confirm")
        lvl.update(0.016)
        self.assertTrue(lvl.decision_system.is_active())

        dec = lvl.decision_system.current_decision
        dec.selected_index = next(i for i, o in enumerate(dec.options) if o.get("safe"))
        lvl.decision_system.handle_input("confirm")
        self.assertTrue(lvl._mayor_assisted)

        lvl._interact_siren()
        lvl._siren_success()
        self.assertTrue(lvl._siren_sounded)

        lvl._interact_stairs()
        lvl._stairs_success()
        self.assertTrue(lvl._ridge_climbed)

        lvl.on_trigger_activated("ridge_safe")
        self.assertTrue(lvl.completed)
        lvl.draw(self.surf)

    def test_final_mission(self):
        """Test Final Mission shutdown flow."""
        lvl = FinalMissionShutdownMachine(self.game)
        voss = next(n for n in lvl.npcs if n.name == "Dr. Elias Voss")
        lvl.on_npc_interacted(voss)
        for _ in range(8):
            if lvl.active_dialogue is None:
                break
            lvl.handle_input("confirm")
        lvl.update(0.016)
        self.assertTrue(lvl.decision_system.is_active())

        # Step 1 decision
        dec1 = lvl.decision_system.current_decision
        dec1.selected_index = next(i for i, o in enumerate(dec1.options) if o.get("safe"))
        lvl.decision_system.handle_input("confirm")
        self.assertTrue(lvl._voss_confronted)

        # Bypass mini-game
        lvl._interact_bypass()
        lvl.minigame = None
        lvl._bypass_success()
        self.assertTrue(lvl._depressurized)

        # Step 2 decision
        lvl.on_npc_interacted(voss)
        for _ in range(8):
            if lvl.active_dialogue is None:
                break
            lvl.handle_input("confirm")
        lvl.update(0.016)
        self.assertTrue(lvl.decision_system.is_active())
        dec2 = lvl.decision_system.current_decision
        dec2.selected_index = next(i for i, o in enumerate(dec2.options) if o.get("safe"))
        lvl.decision_system.handle_input("confirm")

        # Scram mini-game
        lvl._interact_scram()
        lvl.minigame = None
        lvl._scram_success()
        self.assertTrue(lvl._core_scrammed)
        self.assertTrue(lvl.completed)
        lvl.draw(self.surf)

    def test_chapter_transition_recaps(self):
        """Test that all chapter milestone recaps render properly."""
        for ch in ("prologue", "chapter_1", "chapter_2", "chapter_3", "chapter_4", "chapter_5"):
            self.assertIn(ch, CHAPTER_RECAPS)
            trans = StoryTransitionState(
                self.game, "chapter_2", "level_1_fire",
                is_chapter_end=True, completed_ch=ch
            )
            trans.draw(self.surf)


if __name__ == "__main__":
    unittest.main()
