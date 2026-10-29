"""Data and campaign invariants for the playable story route."""
import json
import unittest
from collections import deque
from pathlib import Path
from unittest.mock import patch

from src.core.session import GameSession
import pygame

from src.world.island_geometry import BRIDGES, IslandGeometry
from src.world.island_routes import campaign_route_for_region, shortest_route
from src.world.island_world import MAP_SCALE, MAP_SIZE, REGION_ANCHORS, WORLD_SIZE


ROOT = Path(__file__).resolve().parents[1]


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


class CampaignIntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.campaign = read_json(ROOT / "data" / "campaign.json")
        cls.stages = {
            stage_id: read_json(ROOT / "data" / "stages" / f"{stage_id}.json")
            for stage_id in GameSession.STAGE_ORDER
        }

    def test_campaign_order_has_a_stage_file_for_each_entry(self):
        self.assertEqual(len(GameSession.STAGE_ORDER), 22)
        self.assertEqual(len(set(GameSession.STAGE_ORDER)), len(GameSession.STAGE_ORDER))
        declared = [stage["id"] for stage in self.campaign["stages"]]
        self.assertEqual(declared, GameSession.STAGE_ORDER)
        self.assertEqual(set(self.stages), set(GameSession.STAGE_ORDER))

    def test_central_town_order_and_hazard_buildup_follow_the_story(self):
        central_town = [stage for stage in self.campaign["stages"]
                        if stage["region"] == "Central Town"]
        expected_ids = [
            "flash_fire", "central_earthquake", "central_typhoon", "central_flash_flood"
        ]
        expected_hazards = [
            ["flash_fire"],
            ["flash_fire", "earthquake"],
            ["flash_fire", "earthquake", "typhoon"],
            ["flash_fire", "earthquake", "typhoon", "flash_flood"],
        ]
        self.assertEqual([stage["id"] for stage in central_town], expected_ids)
        self.assertEqual([stage["active_hazards"] for stage in central_town], expected_hazards)
        for stage_id, hazards in zip(expected_ids, expected_hazards):
            self.assertEqual(self.stages[stage_id]["hazards"]["disasters"], hazards)
        self.assertEqual(GameSession.STAGE_ORDER[5:9], expected_ids)

    def test_old_local_campaign_progress_maps_to_the_replacement_stage(self):
        characters = read_json(ROOT / "data" / "characters.json")
        old_save = {
            "version": 3,
            "campaign_version": 3,
            "character_id": characters[0]["id"],
            "challenger_id": "PLAYER-OLD",
            "challenger_name": "PLAYER-OLD",
            "unlocked": ["home_island_tutorial", "central_landslide", "central_typhoon"],
            "completed": ["central_landslide"],
            "current_stage": "central_landslide",
            "records": {},
            "high_scores": {},
            "campaign_results": {},
        }
        session = GameSession()
        with patch("src.core.session.load_save", return_value=old_save):
            self.assertTrue(session.load(characters))
        self.assertIn("central_earthquake", session.unlocked)
        self.assertIn("central_earthquake", session.completed)
        self.assertEqual(session.current_stage, "central_earthquake")
        self.assertNotIn("central_landslide", session.completed)

    def test_quest_and_rescue_targets_exist(self):
        for stage_id, stage in self.stages.items():
            with self.subTest(stage=stage_id):
                items = {item["id"] for item in stage["items"]}
                npcs = {npc["id"] for npc in stage["npcs"]}
                areas = {area["id"] for area in stage["areas"]}
                for npc in stage["npcs"]:
                    rescue_item = npc.get("rescue_item")
                    if rescue_item:
                        self.assertIn(rescue_item, items, f"NPC {npc['id']} has missing rescue supply")
                for quest in stage["quests"]:
                    kind, target = quest["type"], quest["target"]
                    if kind == "collect":
                        self.assertIn(target, items, f"Missing collect target {target}")
                    elif kind in ("talk", "rescue"):
                        self.assertIn(target, npcs, f"Missing {kind} target {target}")
                    elif kind == "reach":
                        self.assertIn(target, areas, f"Missing reach target {target}")
                    elif kind == "cover":
                        self.assertEqual(target, "earthquake")
                    else:
                        self.fail(f"Unsupported quest type {kind!r}")

    def test_stage_geometry_and_start_positions_are_valid(self):
        for stage_id, stage in self.stages.items():
            with self.subTest(stage=stage_id):
                width, height = stage["map_size"]
                self.assertGreater(width, 0)
                self.assertGreater(height, 0)
                x, y = stage["player_start"]
                self.assertTrue(0 <= x < width and 0 <= y < height)
                for rect in [*stage["walls"], *(area["rect"] for area in stage["areas"]),
                             *stage.get("safe_zones", [])]:
                    rx, ry, rw, rh = rect
                    self.assertGreater(rw, 0)
                    self.assertGreater(rh, 0)
                    self.assertGreaterEqual(rx, 0)
                    self.assertGreaterEqual(ry, 0)
                    self.assertLessEqual(rx + rw, width)
                    self.assertLessEqual(ry + rh, height)

    def test_map_art_references_exist(self):
        world_map = read_json(ROOT / "data" / "world_map.json")
        for page in world_map["pages"]:
            with self.subTest(image=page["image"]):
                self.assertTrue((ROOT / page["image"]).is_file())
        routes = read_json(ROOT / "data" / "island_routes.json")
        self.assertTrue((ROOT / routes["map_asset"]).is_file())

    def test_supplied_island_map_defines_connected_campaign_routes(self):
        routes = read_json(ROOT / "data" / "island_routes.json")
        route = routes["campaign_route"]
        self.assertEqual(route[0], routes["region_stops"]["Home Village"])
        self.assertEqual(route[-1], routes["region_stops"]["Main Control Room"])
        for stage in self.campaign["stages"]:
            region = stage["region"]
            with self.subTest(stage=stage["id"], region=region):
                self.assertIn(region, routes["region_stops"])
        for current, destination in zip(route, route[1:]):
            with self.subTest(route=f"{current}->{destination}"):
                stops, points = shortest_route(routes, current, destination)
                self.assertGreaterEqual(len(stops), 2)
                self.assertEqual((stops[0], stops[-1]), (current, destination))
                self.assertGreaterEqual(len(points), 2)
                self.assertTrue(all(0 <= x <= 1 and 0 <= y <= 1 for x, y in points))
        self.assertEqual(campaign_route_for_region(routes, "Main Control Room")[1], None)

    def test_world_anchors_match_the_approved_map_coordinates(self):
        self.assertEqual(REGION_ANCHORS, {
            "Home Village": (230, 472),
            "North West Plateau": (300, 330),
            "Central Town": (492, 596),
            "Harbor": (181, 749),
            "North East Plains": (1177, 416),
            "Volcano Valleys": (526, 415),
            "Main Control Room": (785, 226),
        })
        self.assertEqual(len(BRIDGES), 4)
        self.assertEqual([bridge["point"] for bridge in BRIDGES], [
            (325, 501), (316, 724), (979, 547), (945, 785),
        ])

    def test_every_campaign_route_leg_is_reachable_over_land_and_accepted_crossings(self):
        pygame.init()
        geometry = IslandGeometry()
        routes = read_json(ROOT / "data" / "island_routes.json")

        def world_point(stop_id):
            nx, ny = routes["stops"][stop_id]["point"]
            return (round(nx * MAP_SIZE[0] * MAP_SCALE),
                    round(ny * MAP_SIZE[1] * MAP_SCALE))

        def reachable(start_id, goal_id):
            step = 8
            start = tuple((coordinate // step) * step
                          for coordinate in world_point(start_id))
            goal = tuple((coordinate // step) * step
                         for coordinate in world_point(goal_id))
            pending = deque([start])
            visited = {start}
            while pending:
                x, y = pending.popleft()
                if abs(x - goal[0]) <= step and abs(y - goal[1]) <= step:
                    return True
                for dx, dy in ((step, 0), (-step, 0), (0, step), (0, -step)):
                    candidate = (x + dx, y + dy)
                    if candidate in visited:
                        continue
                    if (candidate[0] < 0 or candidate[1] < 0
                            or candidate[0] >= WORLD_SIZE[0]
                            or candidate[1] >= WORLD_SIZE[1]):
                        continue
                    probe = pygame.Rect(candidate[0] - 5, candidate[1] - 5, 12, 12)
                    if geometry.is_blocked(probe):
                        continue
                    visited.add(candidate)
                    pending.append(candidate)
            return False

        route = routes["campaign_route"]
        self.assertEqual(route[1], "nw_plateau")
        for start, destination in zip(route, route[1:]):
            with self.subTest(leg=f"{start}->{destination}"):
                self.assertTrue(reachable(start, destination))

    def test_pulong_is_not_a_walkable_campaign_stop(self):
        routes = read_json(ROOT / "data" / "island_routes.json")
        self.assertNotIn("pulong", routes["campaign_route"])
        self.assertEqual(shortest_route(routes, "pulong", "bayani"), ([], []))

    def test_chapter_openers_are_short_character_scenes_at_story_boundaries(self):
        openers = read_json(ROOT / "data" / "chapter_openers.json")
        self.assertEqual(set(openers), {
            "home_island_tutorial", "earthquake", "flash_fire",
            "harbor_flash_flood", "plains_typhoon", "silence_volcano",
            "final_shutdown",
        })
        for stage_id, opener in openers.items():
            with self.subTest(stage=stage_id):
                self.assertTrue(opener["chapter"].strip())
                self.assertTrue(opener["place"].strip())
                self.assertEqual(len(opener["dialogue"]), 2)
                self.assertTrue(opener["scene"].strip())
                for line in opener["dialogue"]:
                    self.assertTrue(line["speaker"].strip())
                    self.assertLessEqual(len(line["line"].split()), 15)
                    self.assertNotIn("tarsi", line["speaker"].lower())

    def test_campaign_uses_the_supplied_named_npc_roster(self):
        campaign_cast = {
            npc["name"]
            for stage in self.stages.values()
            for npc in stage["npcs"]
        }
        expected = {
            "Lola Teresa", "Dr. Mira Santos", "Rico Dela Cruz", "Mang Lito",
            "Dr. Elena Reyes", "Tito Ramon", "Dr. Elias Voss", "Engr. Paolo Santos",
            "Aling Rosa", "Jun", "Berto", "Liza", "Mayor Cruz", "Nurse Joy",
            "Captain Reyes", "Sari", "Kuya Ben", "Mila", "Tatay Pio", "Rhea",
        }
        self.assertTrue(expected <= campaign_cast,
                        f"Missing roster characters: {sorted(expected - campaign_cast)}")

    def test_npc_dialogue_is_present_and_matches_each_scene_hazard(self):
        for stage_id, stage in self.stages.items():
            with self.subTest(stage=stage_id):
                for npc in stage["npcs"]:
                    self.assertTrue(npc["dialogue"])
                    self.assertTrue(npc["after_dialogue"])
                    self.assertTrue(all(line.strip() for line in npc["dialogue"]))
        expected_terms = {
            "earthquake": ("aftershock", "cover"),
            "tsunami": ("tsunami", "uphill"),
            "flash_fire": ("fire", "smoke"),
            "central_flash_flood": ("floodwater", "raised road"),
            "harbor_fire_tsunami": ("fire", "tsunami"),
            "volcano_flash_flood": ("lahar", "ash"),
            "final_typhoon_flood": ("eight hazard", "floodwater"),
            "final_shutdown": ("world engine", "shutdown"),
        }
        for stage_id, terms in expected_terms.items():
            speech = " ".join(
                line.lower()
                for npc in self.stages[stage_id]["npcs"]
                for line in npc["dialogue"] + npc["after_dialogue"]
            )
            with self.subTest(stage=stage_id):
                for term in terms:
                    self.assertIn(term, speech)


if __name__ == "__main__":
    unittest.main()
