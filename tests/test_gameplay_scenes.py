"""Headless construction, rendering, and evacuation checks for campaign scenes."""
import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import json
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pygame

from src.core import settings
from src.core.session import GameSession
from src.entities.item_art import _item_kind, draw_item
from src.entities.npc import NPC
from src.entities.player import Player
from src.entities.reference_art import GAME_ART_DIR, effect_frame, npc_walk_sheet_for, sprite
from src.states.big_map import BigMap
from src.states.stage_complete import StageComplete
from src.ui import theme
from src.world.island_geometry import BRIDGES, DOCKS, IslandGeometry
from src.world.scene_art import SceneArt
from src.world.island_world import (
    REGION_ANCHORS, REGION_PLACEMENT_BOUNDS, WORLD_SIZE, map_to_world,
    region_for_stage, world_to_map,
)


ROOT = Path(__file__).resolve().parents[1]


class GameplaySceneTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT))
        cls.surface = pygame.Surface((settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT))
        cls.characters = json.loads((ROOT / "data" / "characters.json").read_text(encoding="utf-8"))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def make_game(self):
        session = GameSession()
        session.character = self.characters[0]
        return SimpleNamespace(session=session)

    def test_every_campaign_scene_constructs_updates_and_draws(self):
        for stage_id in GameSession.STAGE_ORDER:
            with self.subTest(stage=stage_id):
                scene = BigMap(self.make_game(), stage_id)
                scene.update(1 / 60)
                theme.TEXT_QUEUE.clear()
                scene.draw(self.surface)
                self.assertEqual(self.surface.get_size(), (320, 180))
                self.assertGreaterEqual(len(scene.quests.quests), 1)
                self.assertEqual((scene.map_width, scene.map_height), WORLD_SIZE)
                self.assertEqual(set(scene.region_arts), {
                    "Home Village", "North West Plateau", "Central Town", "Harbor",
                    "North East Plains", "Volcano Valleys", "Main Control Room",
                })
                theme.TEXT_QUEUE.clear()

    def test_region_starts_align_to_approved_map_anchors(self):
        cases = (
            ("home_island_tutorial", "Home Village"),
            ("earthquake", "North West Plateau"),
            ("flash_fire", "Central Town"),
            ("harbor_flash_flood", "Harbor"),
            ("plains_typhoon", "North East Plains"),
            ("silence_volcano", "Volcano Valleys"),
            ("final_shutdown", "Main Control Room"),
        )
        for stage_id, region in cases:
            with self.subTest(region=region):
                scene = BigMap(self.make_game(), stage_id)
                anchor = map_to_world(REGION_ANCHORS[region])
                self.assertLessEqual(abs(scene.player.rect.x - anchor[0]), 1)
                self.assertLessEqual(abs(scene.player.rect.y - anchor[1]), 1)

    def test_camera_and_character_scale_stay_consistent_with_establishments(self):
        scene = BigMap(self.make_game(), "earthquake")
        self.assertEqual(scene.camera.zoom, 0.82)
        self.assertEqual(scene.player.sheet.size[1], 20)
        self.assertLess(NPC.WORLD_SPRITE_SIZE[1], 30)
        self.assertEqual(scene.camera.zoom, 0.82)  # no dialogue/disaster zoom jump

    def test_supplied_reference_pack_assets_are_available_to_live_renderers(self):
        for name in ("juan", "maria"):
            with self.subTest(player=name):
                for row in range(4):
                    for column in range(6):
                        self.assertTrue((GAME_ART_DIR / "player_frames" /
                                         f"{name}_{row}_{column}.png").is_file())
        for name in ("lola_teresa", "dr_mira_santos", "rico_dela_cruz", "mang_lito",
                     "dr_elena_reyes", "tito_ramon", "dr_elias_voss", "engr_paolo_santos",
                     "aling_rosa", "jun", "berto", "liza", "mayor_cruz", "nurse_joy",
                     "captain_reyes", "sari", "kuya_ben", "mila", "tatay_pio", "rhea"):
            with self.subTest(npc=name):
                sheet = sprite("characters", name)
                self.assertIsNotNone(sheet)
                self.assertEqual((sheet.get_width() % 4, sheet.get_height() % 4), (0, 0))
        self.assertIsNotNone(sprite("terrain", "grass"))
        self.assertIsNotNone(sprite("buildings", "building_19"))  # reference bridge
        self.assertIsNotNone(sprite("items", "first_aid"))
        self.assertEqual(effect_frame("fire", (31, 36), 0.25).get_size(), (31, 36))
        for name in ("house_small", "evacuation_center", "bridge", "dock", "school"):
            with self.subTest(building=name):
                art = sprite("buildings", name)
                self.assertIsNotNone(art)
                self.assertGreater(art.get_bounding_rect().width, 10)
                self.assertGreater(art.get_bounding_rect().height, 10)

    def test_supply_icons_render_at_pickup_scale(self):
        with patch("src.entities.item_art.scaled",
                   side_effect=lambda _category, _name, size:
                   pygame.Surface(size, pygame.SRCALPHA)) as load_art:
            draw_item(pygame.Surface((40, 40)), pygame.Rect(16, 16, 8, 8),
                      "medkit", (240, 60, 60), "First-aid kit")
        self.assertEqual(load_art.call_args.args[2], (12, 12))

    def test_live_player_npc_and_stage_use_reference_animation_and_terrain(self):
        player = Player(10, 10, walk_path="assets/images/characters/juan_walk.png")
        self.assertEqual(player.sheet.size[1], 20)
        player.sheet.update(0.2, -1, 0)
        self.assertEqual(player.sheet.facing, "left")
        person = NPC({"id": "berto", "name": "Berto", "pos": [20, 20],
                      "color": [60, 120, 180], "dialogue": ["Hello"]})
        self.assertIsNotNone(person.walk_sheet)
        scene_data = json.loads((ROOT / "data/stages/earthquake.json").read_text(encoding="utf-8"))
        art = SceneArt(scene_data, "earthquake")
        self.assertIsNotNone(art.reference_ground)

    def test_reference_buildings_scale_once_into_world_pixels(self):
        camera = SimpleNamespace(zoom=0.82, offset=pygame.Vector2(),
                                 viewport=pygame.Rect(0, 0, 320, 180))
        surface = pygame.Surface((320, 180))
        art = pygame.Surface((1, 1), pygame.SRCALPHA)
        with patch("src.world.island_geometry.scaled", return_value=art) as load_art:
            IslandGeometry._house(surface, camera, 100, 100)
            self.assertEqual(load_art.call_args.args[2], (33, 26))

            IslandGeometry._landmark_building(
                surface, camera, 100, 100, "school", width=25, height=18)
            self.assertEqual(load_art.call_args.args[2], (41, 36))

    def test_evacuation_center_art_fits_its_objective_footprint(self):
        surface = pygame.Surface((320, 180))
        objective = pygame.Rect(210, 154, 72, 72)
        art = pygame.Surface((1, 1), pygame.SRCALPHA)
        with patch("src.world.scene_art.scaled", return_value=art) as load_art:
            SceneArt.draw_shelter(surface, objective)
        self.assertEqual(load_art.call_args.args[2], (58, 58))

    def test_player_water_collision_blocks_open_water(self):
        geometry = IslandGeometry()
        point = map_to_world((365, 400))
        probe = pygame.Rect(point[0] - 6, point[1] - 6, 12, 12)
        self.assertTrue(geometry.is_blocked(probe))
        self.assertTrue(geometry.is_blocked(
            pygame.Rect(*map_to_world((1150, 600)), 12, 12)))  # Talon wetland
        self.assertTrue(geometry.is_blocked(
            pygame.Rect(*map_to_world((675, 820)), 12, 12)))  # Pulong scenery
        self.assertFalse(geometry.is_blocked(
            pygame.Rect(*map_to_world((1150, 450)), 12, 12)))  # ordinary Bayani land
        self.assertGreaterEqual(len(DOCKS), 2)
        self.assertFalse(geometry.is_blocked(
            pygame.Rect(*map_to_world((181, 749)), 12, 12)))  # connected Harboro dock

        player = Player(point[0] - 36, point[1] - 6, speed=120)
        player.get_direction = lambda: pygame.Vector2(1, 0)
        for _ in range(90):
            player.update(1 / 60, [], collision=geometry)
        self.assertLess(player.rect.centerx, point[0] - 10)

    def test_player_can_cross_at_each_of_the_four_accepted_bridges(self):
        geometry = IslandGeometry()
        endpoints = {
            "crossing_1": ((295, 501), (355, 501), pygame.Vector2(1, 0)),
            "crossing_2": ((286, 724), (346, 724), pygame.Vector2(1, 0)),
            "crossing_3": ((949, 547), (1009, 547), pygame.Vector2(1, 0)),
            "crossing_4_baybay": ((920, 785), (970, 785), pygame.Vector2(1, 0)),
        }
        self.assertEqual({bridge["id"] for bridge in BRIDGES}, set(endpoints))
        for bridge_id, (start, end, direction) in endpoints.items():
            with self.subTest(bridge=bridge_id):
                world_start, world_end = map_to_world(start), map_to_world(end)
                player = Player(world_start[0] - 6, world_start[1] - 6, speed=140)
                player.get_direction = lambda d=direction: d
                for _ in range(120):
                    player.update(1 / 60, [], collision=geometry)
                if direction.x:
                    self.assertGreaterEqual(player.rect.centerx, world_end[0] - 8)
                else:
                    self.assertGreaterEqual(player.rect.centery, world_end[1] - 8)

    def test_all_campaign_mission_objects_are_walkable_and_reachable(self):
        for stage_id in GameSession.STAGE_ORDER:
            scene = BigMap(self.make_game(), stage_id)
            geometry = scene.island_geometry
            start = scene.player.rect
            with self.subTest(stage=stage_id, object="player_start"):
                self.assertFalse(geometry.is_blocked(start))

            targets = [
                (f"NPC {npc.id}", npc.rect) for npc in scene.npcs
            ] + [
                (f"item {item['id']}", item["rect"]) for item in scene.items
            ] + [
                (f"area {area['id']}", area["rect"]) for area in scene.areas
            ] + [
                (f"safe zone {index}", zone) for index, zone in
                enumerate(scene.safe_zones + scene.cover_spots)
            ]
            for label, goal in targets:
                with self.subTest(stage=stage_id, object=label):
                    self.assertFalse(geometry.is_blocked(goal),
                                     f"{label} footprint enters water or leaves the coast")
                    map_center = world_to_map(goal.center)
                    left, top, right, bottom = REGION_PLACEMENT_BOUNDS[
                        region_for_stage(stage_id)
                    ]
                    self.assertTrue(left <= map_center[0] <= right
                                    and top <= map_center[1] <= bottom,
                                    f"{label} is outside its assigned map region")
                    path = geometry.find_path(start.center, goal)
                    self.assertTrue(path or start.colliderect(goal),
                                    f"{label} cannot be reached from the player start")

    def test_randomized_items_never_overlap_each_other_or_mission_actors(self):
        for stage_id in GameSession.STAGE_ORDER:
            scene = BigMap(self.make_game(), stage_id)
            with self.subTest(stage=stage_id):
                for index, item in enumerate(scene.items):
                    for other in scene.items[index + 1:]:
                        self.assertFalse(
                            item["rect"].inflate(12, 12).colliderect(other["rect"]),
                            f"{item['id']} overlaps {other['id']}",
                        )
                    self.assertFalse(
                        any(item["rect"].colliderect(npc.rect.inflate(12, 12))
                            for npc in scene.npcs),
                        f"{item['id']} overlaps an NPC",
                    )
                    self.assertFalse(
                        any(item["rect"].colliderect(area["rect"].inflate(8, 8))
                            for area in scene.areas),
                        f"{item['id']} overlaps a mission destination",
                    )

    def test_stage_specific_item_ids_use_their_real_guide_item_type(self):
        cases = {
            ("central_typhoon_supply", "Battery radio"): "radio",
            ("landslide_supply", "First-aid kit"): "first_aid",
            ("calm_before_wave_supply", "Community checklist"): "documents",
            ("harbor_fire_tsunami_supply", "Fire blanket"): "fire_blanket",
            ("backup_cell", "Emergency system backup cell"): "battery",
        }
        for (item_id, item_name), expected in cases.items():
            with self.subTest(item=item_id):
                self.assertEqual(_item_kind(item_id, item_name), expected)

    def test_every_campaign_escort_can_reach_its_evacuation_destination(self):
        for stage_id in GameSession.STAGE_ORDER:
            scene = BigMap(self.make_game(), stage_id)
            destination = next(iter(scene.area_goals.values()))
            for npc in scene.npcs:
                with self.subTest(stage=stage_id, npc=npc.id):
                    path = scene.island_geometry.find_path(
                        npc.rect.center, destination,
                        actor_size=npc.rect.size,
                    )
                    self.assertTrue(path or destination.colliderect(npc.rect),
                                    f"{npc.id} cannot reach the evacuation destination")

    def test_island_overview_is_available_during_play(self):
        scene = BigMap(self.make_game(), "home_island_tutorial")
        scene.map_open = True
        theme.TEXT_QUEUE.clear()
        scene.draw(self.surface)
        queued_text = [entry[1] for entry in theme.TEXT_QUEUE]
        self.assertTrue(any(label.startswith("YOU ARE HERE") for label in queued_text))
        self.assertTrue(any("SAN ISIDRO" in label for label in queued_text))
        self.assertIn("NEXT CHAPTER", queued_text)
        self.assertIn("NORTH WEST PLATEAU", queued_text)
        self.assertIn("HOME VILLAGE", queued_text)
        self.assertIn("M CLOSE  ·  TAB PLACES", queued_text)
        theme.TEXT_QUEUE.clear()

        scene.player.rect.center = map_to_world((492, 596))
        theme.TEXT_QUEUE.clear()
        scene.draw(self.surface)
        queued_text = [entry[1] for entry in theme.TEXT_QUEUE]
        self.assertTrue(any("SANTOS" == label for label in queued_text))
        self.assertIn("NEXT CHAPTER", queued_text)
        self.assertIn("HARBORO", queued_text)
        self.assertIn("CENTRAL TOWN", queued_text)
        theme.TEXT_QUEUE.clear()

    def test_island_location_marker_follows_the_player_across_regions(self):
        scene = BigMap(self.make_game(), "home_island_tutorial")
        self.assertEqual(scene.player_map_stop(), "san_isidro")
        scene.player.rect.center = map_to_world((492, 596))
        self.assertEqual(scene.player_map_stop(), "santos")
        scene.player.rect.center = map_to_world((1177, 416))
        self.assertEqual(scene.player_map_stop(), "bayani")
        final_scene = BigMap(self.make_game(), "final_shutdown")
        self.assertEqual(final_scene.player_map_stop(), "mount_talon")

    def test_residents_can_reach_the_scene_evacuation_destination(self):
        resident_count = 0
        for stage_id in GameSession.STAGE_ORDER:
            scene = BigMap(self.make_game(), stage_id)
            if not scene.npcs or not scene.area_goals:
                continue
            destination = next(iter(scene.area_goals.values()))
            for npc in scene.npcs:
                resident_count += 1
                npc.evacuate(destination, scene.navigation_walls,
                             (scene.map_width, scene.map_height), scene.island_geometry)
                for _ in range(600):
                    npc.update(0.1, scene.navigation_walls, scene.island_geometry)
                    self.assertFalse(scene.island_geometry.is_blocked(npc.rect),
                                     f"{stage_id}: {npc.id} stepped into water")
                    if npc.evacuated:
                        break
                self.assertTrue(npc.evacuated, f"{stage_id}: {npc.name} did not reach the refuge")
        self.assertGreaterEqual(resident_count, 30)

    def test_mission_2_berto_reaches_shelter_without_crossing_water(self):
        scene = BigMap(self.make_game(), "earthquake")
        berto = next(npc for npc in scene.npcs if npc.id == "kapitan_jo")
        refuge = next(iter(scene.area_goals.values()))
        berto.evacuate(refuge, scene.navigation_walls,
                       (scene.map_width, scene.map_height), scene.island_geometry)
        for _ in range(1200):
            berto.update(1 / 30, scene.navigation_walls, scene.island_geometry)
            self.assertFalse(scene.island_geometry.is_blocked(berto.rect))
            if berto.evacuated:
                break
        self.assertTrue(berto.evacuated, "Berto must reach the Mission 2 evacuation area")

    def test_mission_2_player_arrival_waits_for_the_required_npc(self):
        scene = BigMap(self.make_game(), "earthquake")
        self.assertEqual(scene.required_evacuation_npc_id, "kapitan_jo")
        scene.evacuation_started = True
        scene.evacuation_reached = True

        self.assertFalse(scene.try_finish_evacuation())
        self.assertFalse(scene.finished)
        self.assertEqual(scene.mission2_evacuation_status(), "WAITING FOR BERTO")
        theme.TEXT_QUEUE.clear()
        scene.draw_status(self.surface)
        self.assertIn("WAITING FOR BERTO", [entry[1] for entry in theme.TEXT_QUEUE])
        theme.TEXT_QUEUE.clear()

    def test_mission_2_npc_arrival_waits_for_the_player(self):
        scene = BigMap(self.make_game(), "earthquake")
        scene.evacuation_started = True
        scene.npcs[0].evacuated = True

        self.assertFalse(scene.try_finish_evacuation())
        self.assertFalse(scene.finished)
        self.assertEqual(scene.mission2_evacuation_status(), "WAITING FOR PLAYER")
        theme.TEXT_QUEUE.clear()
        scene.draw_status(self.surface)
        self.assertIn("WAITING FOR PLAYER", [entry[1] for entry in theme.TEXT_QUEUE])
        theme.TEXT_QUEUE.clear()

    def test_mission_2_finishes_once_after_both_arrive(self):
        scene = BigMap(self.make_game(), "earthquake")
        scene.evacuation_started = True
        scene.evacuation_reached = True
        scene.npcs[0].evacuated = True

        self.assertTrue(scene.try_finish_evacuation())
        self.assertTrue(scene.finished)
        finish_timer = scene.finish_timer
        self.assertFalse(scene.try_finish_evacuation())
        self.assertEqual(scene.finish_timer, finish_timer)
        self.assertEqual(scene.mission2_evacuation_status(),
                         "BOTH ARRIVED · MISSION COMPLETE")

    def test_expanded_task_list_hides_while_a_modal_is_open(self):
        scene = BigMap(self.make_game(), "earthquake")
        scene.show_all_quests = True
        scene.dialogue.open("KAPITAN JO", ["Take cover, then move to safety."])
        scene.dialogue.chars = 10_000
        theme.TEXT_QUEUE.clear()
        scene.draw(self.surface)
        self.assertNotIn("MISSION TASKS", [entry[1] for entry in theme.TEXT_QUEUE])

        scene.dialogue.active = False
        scene.choice.open("KAPITAN JO", "Choose safely", [{"text": "Move to safety"}], lambda _option: None)
        theme.TEXT_QUEUE.clear()
        scene.draw(self.surface)
        self.assertNotIn("MISSION TASKS", [entry[1] for entry in theme.TEXT_QUEUE])

        scene.choice.active = False
        theme.TEXT_QUEUE.clear()
        scene.draw(self.surface)
        self.assertIn("MISSION TASKS", [entry[1] for entry in theme.TEXT_QUEUE])
        theme.TEXT_QUEUE.clear()

    def test_task_tab_suppresses_tarsier_bubble(self):
        scene = BigMap(self.make_game(), "earthquake")
        scene.show_all_quests = True
        scene.mascot.say("Keep an eye on the river crossing.", 5)
        scene.draw(self.surface)
        self.assertNotIn("Keep an eye on the river crossing.",
                         [entry[1] for entry in theme.TEXT_QUEUE])
        theme.TEXT_QUEUE.clear()

    def test_island_map_shows_full_route_and_next_stop_from_live_position(self):
        scene = BigMap(self.make_game(), "plains_typhoon")
        scene.map_open = True
        theme.TEXT_QUEUE.clear()
        scene.draw(self.surface)
        rendered = [entry[1] for entry in theme.TEXT_QUEUE]
        self.assertIn("STORY ROUTE", rendered)
        self.assertIn("YOU ARE HERE", rendered)
        self.assertIn("PAG-ASA", rendered)
        self.assertEqual(scene.player_map_stop(), "bayani")
        self.assertEqual(scene.story_map_destination("bayani"), "pag_asa")
        theme.TEXT_QUEUE.clear()

    def test_mission_transition_shows_results_without_narrator_story_card(self):
        game = self.make_game()
        stats = {
            "stage_id": "calm_before_wave", "mission_number": 4,
            "chapter": "North West Plateau", "lessons": ["Check official alerts."],
            "consequences": ["The warning tower has unstable readings."],
            "time": 60, "damage": 0, "property_damage": 0,
            "items_found": 2, "items_total": 4, "quests_done": 3,
            "quests_total": 5, "score": 700,
        }
        transition = StageComplete(game, stats)
        theme.TEXT_QUEUE.clear()
        transition.draw(self.surface)
        queued_text = [entry[1] for entry in theme.TEXT_QUEUE]
        self.assertIn("MISSION COMPLETE!", queued_text)
        self.assertNotIn("NANAY LUZ", queued_text)
        self.assertNotIn("COMMUNITY RADIO", queued_text)
        self.assertIn("AUTO 13s · ENTER TO CONTINUE", queued_text)
        theme.TEXT_QUEUE.clear()


if __name__ == "__main__":
    unittest.main()
