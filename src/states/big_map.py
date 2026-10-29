import random
import math
from types import SimpleNamespace

import pygame

from src.ui import theme
from src.core import settings
from src.core.event_bus import EventBus
from src.entities.mascot import Mascot
from src.entities.npc import NPC
from src.entities.item_art import draw_item
from src.entities.player import Player
from src.entities.reference_art import effect_frame
from src.hazards.debris import Debris
from src.hazards.rain import Rain
from src.hazards.wind import Wind
from src.states.base_state import BaseState
from src.states.game_over import GameOver
from src.states.stage_complete import StageComplete
from src.systems.quest_system import QuestSystem
from src.systems.disaster_system import DisasterSystem
from src.ui.choice_box import ChoiceBox
from src.ui.dialogue_box import DialogueBox
from src.utils.data_loader import BASE_DIR, load_json
from src.utils.helpers import wrap_text
from src.world.camera import Camera
from src.world.island_world import (
    CELL_SIZE, MAP_SIZE, REGION_ANCHORS, REGION_PLACEMENT_BOUNDS, REGION_SCENES, WORLD_SIZE,
    RegionCamera, local_to_world_rect, origin_for_region, origin_for_stage,
    region_for_stage, world_to_map,
)
from src.world.island_geometry import IslandGeometry
from src.world.island_routes import (
    load_island_routes, shortest_route,
)
from src.world.scene_art import SceneArt
from src.core import audio

TILE = 16

# (below this danger value, name, color)
LEVELS = [
    (25, "NORMAL", (110, 230, 130)),
    (50, "WATCH", (255, 220, 80)),
    (75, "WARNING", (255, 150, 50)),
    (101, "CRITICAL", (255, 80, 80)),
]


class BigMap(BaseState):
    _route_map_cache = None

    def __init__(self, game, stage_id="typhoon"):
        super().__init__(game)
        self.stage_id = stage_id
        self.data = load_json(f"data/stages/{stage_id}.json")
        self.font = theme.get_font("tiny")

        self.local_map_width, self.local_map_height = self.data["map_size"]
        w, h = self.local_map_width, self.local_map_height
        self.map_width, self.map_height = WORLD_SIZE
        self.local_player_start = tuple(self.data["player_start"])
        self.region_origin = origin_for_stage(stage_id, self.local_player_start)
        self.route_data = load_island_routes()
        self.active_region = region_for_stage(stage_id)
        if BigMap._route_map_cache is None:
            BigMap._route_map_cache = pygame.image.load(
                str(BASE_DIR / self.route_data["map_asset"])
            ).convert()
        self.route_map_art = BigMap._route_map_cache
        self.scene_art = SceneArt(self.data, stage_id)

        # Mission scenes retain their existing local geometry. Their origins
        # now follow the named map anchors instead of a fabricated 3x2 grid.
        self.island_geometry = IslandGeometry()
        self.region_arts = {}
        self.region_wall_visuals = []
        self.walls = [
            pygame.Rect(0, 0, self.map_width, 8),
            pygame.Rect(0, self.map_height - 8, self.map_width, 8),
            pygame.Rect(0, 0, 8, self.map_height),
            pygame.Rect(self.map_width - 8, 0, 8, self.map_height),
        ]
        for region, representative_stage in REGION_SCENES.items():
            if region == self.active_region:
                region_data, region_art = self.data, self.scene_art
                wall_stage = stage_id
                origin = self.region_origin
            else:
                region_data = load_json(f"data/stages/{representative_stage}.json")
                region_art = SceneArt(region_data, representative_stage)
                wall_stage = representative_stage
                origin = origin_for_region(region, tuple(region_data["player_start"]))
            self.region_arts[region] = (region_art, origin, wall_stage)
            for wall_data in region_data["walls"]:
                wall = local_to_world_rect(pygame.Rect(*wall_data), origin)
                self.walls.append(wall)
                self.region_wall_visuals.append((wall, wall_stage))
            for collider in region_art.shelter_colliders:
                self.walls.append(local_to_world_rect(collider, origin))

        self.map_walls = [wall for wall, _stage in self.region_wall_visuals]
        # The accepted island rule is water-only collision: terrain and
        # authored scenery do not form invisible maze walls for actors.
        self.navigation_walls = []
        # The walkability mask follows the map coastline and waterways. Its
        # four bridge openings are the only river crossings; connected docks
        # are included by the same geometry source.
        self.waterways = self.island_geometry.waterways
        self.bridge_decks = self.island_geometry.bridge_rects
        self.active_world_rect = pygame.Rect(*self.region_origin, *CELL_SIZE)

        character = game.session.character
        self.difficulty = game.session.difficulty
        self.prep_choice = game.session.prep_choice
        relaxed = self.difficulty == "relaxed"
        challenge = self.difficulty == "challenge"
        health_bonus = (20 if self.prep_choice == "first_aid" else 0) + (15 if relaxed else 0)
        sx, sy = self.local_player_start
        self.player = Player(
            sx + self.region_origin[0], sy + self.region_origin[1],
            speed=character["speed"] * (1.1 if relaxed else 1.0),
            max_health=character["max_health"] + health_bonus,
            walk_path=character.get("walk"),
            color=character["color"],
        )
        self.player.ability = character.get("ability")
        # Reserve a thin, permanent HUD rail. The map is clipped into the space
        # between the rails so it remains fully visible behind the interface.
        self.camera = Camera(self.map_width, self.map_height, zoom=0.82,
                             viewport=(0, 21, 320, 143))
        self.camera.follow(self.player.rect)

        self.npcs = []
        for npc_data in self.data["npcs"]:
            placed = dict(npc_data)
            placed["pos"] = [npc_data["pos"][0] + self.region_origin[0],
                             npc_data["pos"][1] + self.region_origin[1]]
            npc = NPC(placed)
            npc.path_collision = self.island_geometry
            self.npcs.append(npc)
        self.rescue_rewards = set()
        self.carried_npc = None
        self.inventory = set()
        self.areas = [{**a, "rect": local_to_world_rect(pygame.Rect(*a["rect"]),
                                                         self.region_origin)}
                      for a in self.data["areas"]]
        self.items = self._place_mission_items()

        self.events = EventBus()
        self.quests = QuestSystem(self.data["quests"], self.events)
        self.events.subscribe("quest_completed", self.on_quest_completed)
        self.events.subscribe("item_collected", self.on_item)
        self.events.subscribe("person_rescued", self.on_rescued)
        self.dialogue = DialogueBox(self.font)
        self.dialogue_npc = None
        self.choice = ChoiceBox(self.font)
        self.show_all_quests = False

        mascot_config = load_json("data/mascot.json")
        self.mascot = Mascot(
            mascot_config, self.data["mascot"], self.events,
            self.quests, self.font, self.player.rect.center,
        )

        # Hazards
        hz = self.data["hazards"]
        self.ramp = hz["danger_ramp_seconds"] * (1.35 if relaxed else 0.82 if challenge else 1.0)
        self.start_delay = hz["hazard_start_seconds"] * (1.3 if relaxed else 0.72 if challenge else 1.0)
        campaign_order = game.session.STAGE_ORDER
        stage_progress = campaign_order.index(stage_id) / max(1, len(campaign_order) - 1)
        tightening = stage_progress * (0.04 if relaxed else 0.15 if challenge else 0.10)
        self.ramp *= 1.0 - tightening
        self.start_delay *= 1.0 - tightening
        if self.prep_choice == "route_plan":
            self.ramp *= 1.12
            self.start_delay += 5
        self.disasters = list(hz.get("disasters", ["typhoon"] if stage_id == "typhoon" else []))
        self.rain = Rain(hz.get("rain", {"drops": 60})) if "typhoon" in self.disasters else None
        self.wind = Wind(hz.get("wind", {"strength": 45}), self.events) if "typhoon" in self.disasters else None
        self.debris = Debris(hz.get("debris", {"damage": 15, "min_interval": 1.2, "max_interval": 3.5}), (w, h), self.events) if "typhoon" in self.disasters else None
        self.disaster_system = DisasterSystem(self.disasters, (w, h), hz)
        self.local_safe_zones = [pygame.Rect(*r) for r in self.data.get("safe_zones", [])]
        # The green earthquake practice field is cover from shaking, not a
        # flood refuge. Keep it out of the water-safe zone list.
        self.local_safe_zones = [
            zone for zone in self.local_safe_zones
            if not any(cover.colliderect(zone) for cover in self.scene_art.cover_spots)
        ]
        local_areas = [
            {**area, "rect": pygame.Rect(*area["rect"])}
            for area in self.data["areas"]
        ]
        for index, zone in enumerate(self.local_safe_zones):
            matching_building = next((area for area in local_areas
                                      if self.scene_art._is_building(area["name"])
                                      and area["rect"].contains(zone)), None)
            if matching_building:
                self.local_safe_zones[index] = self.scene_art.building_interior(matching_building["rect"])
        ox, oy = self.region_origin
        self.safe_zones = [zone.move(ox, oy) for zone in self.local_safe_zones]
        self.local_cover_spots = list(self.scene_art.cover_spots)
        self.cover_spots = [spot.move(ox, oy) for spot in self.local_cover_spots]
        self.area_goals = {
            area["id"]: self.scene_art.objective_rect(
                {**area, "rect": pygame.Rect(*area["rect"])}
            ).move(ox, oy) for area in self.data["areas"]
        }
        reach_targets = {
            quest["target"] for quest in self.data.get("quests", [])
            if quest.get("type") == "reach"
        }
        self.evacuation_area_ids = reach_targets or {
            area["id"] for area in self.areas
            if any(word in area["name"].lower()
                   for word in ("evacuation", "high ground", "shelter", "safe zone", "inland"))
        }
        self.required_evacuation_npc_id = self.data.get("completion_requires_npc")
        # Earthquake protection requires sturdy furniture, not just being
        # inside an evacuation shelter. The tagged practice table is the cover objective.
        self.quake_safe_zones = self.local_cover_spots
        self.elapsed = 0.0      # drives the danger meter (choices can add to it)
        self.play_time = 0.0    # real time played, shown in results
        self.last_level = "NORMAL"

        # Run statistics
        self.items_found = 0
        self.items_total = len(self.items)
        self.powerup_rng = random.Random(hz.get("seed", 1) ^ 0xB54A)
        self.powerups = []
        self.powerup_timer = self.powerup_rng.uniform(14.0, 22.0)
        self.choice_points = 0
        self.final_decision = ""
        self.property_damage = 0
        self.choice_flags = []
        self.consequences = []

        self.toast = ""
        self.toast_timer = 0.0
        self.finished = False
        self.evacuation_reached = False
        self.finish_timer = 0.0
        self.evacuation_started = False
        self.paused = False
        self.pause_selection = 0
        self.pause_buttons = [pygame.Rect(76, 58 + index * 26, 168, 20) for index in range(3)]
        self.map_open = False
        self.map_page = "route"

    def _place_mission_items(self):
        """Randomize supplies over safe, distinct, reachable land in this region."""
        definitions = self.data.get("items", [])
        if not definitions:
            return []

        region = self.active_region
        left, top, right, bottom = REGION_PLACEMENT_BOUNDS[region]
        ox, oy = self.region_origin
        item_size = (8, 8)
        half_w, half_h = item_size[0] // 2, item_size[1] // 2

        # Keep randomized placements inside both the authored mission scene
        # and its approved map region. Coordinates are local to the stage in
        # JSON and world-space only after this translation.
        min_x = max(0, math.ceil(left * 2 - ox - half_w))
        max_x = min(self.local_map_width - item_size[0],
                    math.floor(right * 2 - ox - half_w))
        min_y = max(0, math.ceil(top * 2 - oy - half_h))
        max_y = min(self.local_map_height - item_size[1],
                    math.floor(bottom * 2 - oy - half_h))

        # Never hide a pickup under the player, an NPC, a mission destination,
        # or an authored cover spot. The gap also makes adjacent pickups easy
        # to distinguish and collect separately.
        reserved = [self.player.rect.inflate(28, 28)]
        reserved.extend(npc.rect.inflate(12, 12) for npc in self.npcs)
        reserved.extend(area["rect"].inflate(8, 8) for area in self.areas)
        reserved.extend(spot.move(ox, oy).inflate(8, 8)
                        for spot in self.scene_art.cover_spots)

        candidates = []
        for y in range(min_y, max_y + 1, 8):
            for x in range(min_x, max_x + 1, 8):
                rect = pygame.Rect(x + ox, y + oy, *item_size)
                if any(rect.colliderect(blocker) for blocker in reserved):
                    continue
                if self.island_geometry.is_blocked(rect):
                    continue
                candidates.append((x, y, rect))

        # System-seeded randomness gives players a fresh layout each run.
        # The authored JSON positions remain untouched for saves and tools.
        rng = random.Random()
        rng.shuffle(candidates)
        placed = []
        start = self.player.rect
        for item in definitions:
            selected = None
            for x, y, rect in candidates:
                if any(rect.colliderect(other["rect"].inflate(12, 12))
                       for other in placed):
                    continue
                if not self.island_geometry.find_path(
                        start.center, rect, self.navigation_walls,
                        actor_size=start.size):
                    continue
                selected = (x, y, rect)
                break
            if selected is None:
                raise ValueError(
                    f"Stage {self.stage_id!r} has {len(definitions)} items but "
                    f"cannot place {item.get('id', 'an item')} on distinct, "
                    "reachable land inside its assigned region."
                )
            x, y, rect = selected
            placed.append({**item, "pos": [x, y], "rect": rect})
        return placed
        self.map_page = "route"

    # ---------- danger meter ----------
    def danger(self):
        return min(100.0, self.elapsed / self.ramp * 100)

    def level_of(self, danger):
        for limit, name, color in LEVELS:
            if danger < limit:
                return name, color
        return LEVELS[-1][1], LEVELS[-1][2]

    # ---------- events ----------
    def on_quest_completed(self, title, **_):
        self.toast = f"QUEST DONE: {title}"
        self.toast_timer = 3.0

    def on_item(self, item_id=None, **_):
        self.items_found += 1
        if item_id:
            self.inventory.add(item_id)

    def on_rescued(self, **_):
        return

    def complete_rescue(self, npc):
        if npc.id in self.rescue_rewards:
            return
        self.rescue_rewards.add(npc.id)
        self.events.emit("person_rescued", npc_id=npc.id, item_id=npc.rescue_item)
        self.toast = f"{npc.name} REACHED SAFETY"
        self.toast_timer = 3.0

    def required_npc_is_safe(self):
        if not self.required_evacuation_npc_id:
            return True
        npc = next((n for n in self.npcs if n.id == self.required_evacuation_npc_id), None)
        return bool(npc and npc.evacuated)

    def mission2_evacuation_status(self):
        """Return the explicit Mission 2 arrival state for its HUD message."""
        if self.stage_id != "earthquake" or not self.evacuation_started:
            return None

        player_arrived = self.evacuation_reached
        npc_arrived = self.required_npc_is_safe()
        npc = next((n for n in self.npcs if n.id == self.required_evacuation_npc_id), None)
        npc_name = npc.name.upper() if npc else "ESCORT"

        if player_arrived and npc_arrived:
            return "BOTH ARRIVED · MISSION COMPLETE"
        if player_arrived:
            return f"WAITING FOR {npc_name}"
        if npc_arrived:
            return "WAITING FOR PLAYER"
        return f"GO TO SAFETY · {npc_name} IS MOVING"

    def evacuation_group_is_safe(self):
        # An unrescued resident is not an escort and must not hold the player
        # hostage at the exit. Wait for anyone the player actually rescued,
        # plus an explicitly required story NPC (for example Aling Nena in
        # mission 2). Other residents are still sent toward safety below.
        return all(
            npc.evacuated
            for npc in self.npcs
            if npc.rescued or npc.id == self.required_evacuation_npc_id
        )

    def begin_evacuation(self):
        """Send remaining residents toward the mission refuge once evacuation starts."""
        if self.evacuation_started:
            return
        self.evacuation_started = True
        refuge = next(iter(self.area_goals.values()), None)
        if refuge is None:
            return
        for npc in self.npcs:
            if not npc.evacuated and not npc.evacuating and not npc.following and not npc.carried:
                npc.evacuate(refuge, self.navigation_walls, (self.map_width, self.map_height),
                             self.island_geometry)

    def try_finish_evacuation(self):
        """Finish only after the player and any mission-required escort are safe."""
        if self.finished or not self.evacuation_reached or not self.evacuation_group_is_safe():
            return False
        if self.stage_id == "final_shutdown":
            if not self.quests.all_critical_done() or not self.final_decision:
                if self.toast_timer <= 0:
                    self.toast = ("COMPLETE THE SHUTDOWN PLAN BEFORE EXITING"
                                  if not self.final_decision else
                                  "SECURE THE KEY, RECORDS, AND BACKUP SYSTEM")
                    self.toast_timer = 3.0
                return False
        self.finished = True
        self.finish_timer = 1.0
        self.toast = "YOU AND YOUR NEIGHBOR REACHED SAFETY · MISSION COMPLETE"
        self.toast_timer = 2.5
        return True

    def nearby_npc(self):
        for npc in self.npcs:
            if not npc.rescued and not npc.carried and npc.is_near(self.player.rect):
                return npc
        return None

    def talk(self, npc):
        self.dialogue_npc = npc
        first_time = not npc.talked
        if npc.rescue_item:
            has_supply = npc.rescue_item in self.inventory
            if npc.rescued:
                lines = npc.rescue_success_dialogue or npc.after_dialogue
            elif has_supply:
                lines = npc.rescue_success_dialogue or ["Thank you. I can make it to the safe zone now."]
            else:
                lines = npc.rescue_dialogue or [npc.rescue_hint]

            def finish_rescue():
                # Rescue NPCs use a separate dialogue path. Count that first
                # conversation too, or their check-in objective can never finish.
                if first_time:
                    npc.talked = True
                    self.events.emit("npc_talked", npc_id=npc.id)
                if has_supply and not npc.rescued:
                    npc.rescued = True
                    if npc.needs_carry:
                        npc.carried = True
                        self.carried_npc = npc
                        self.toast = f"CARRY {npc.name} TO THE SAFE AREA"
                    else:
                        npc.start_following((self.map_width, self.map_height),
                                            self.island_geometry)
                        self.toast = f"{npc.name} WILL FOLLOW YOU TO SAFETY"
                    self.toast_timer = 3.0
                    if npc.choice:
                        self.choice.open(
                            npc.name, npc.choice["prompt"],
                            npc.choice["options"], self.on_choice,
                        )
                elif not has_supply:
                    self.mascot.say(npc.rescue_hint, 5)

            self.dialogue.open(npc.name, lines, finish_rescue)
            return

        lines = npc.get_lines()
        npc.talked = True

        def finish():
            if first_time:
                self.events.emit("npc_talked", npc_id=npc.id)
                if npc.choice:
                    self.choice.open(
                        npc.name, npc.choice["prompt"],
                        npc.choice["options"], self.on_choice,
                    )

        self.dialogue.open(npc.name, lines, finish)

    def on_choice(self, option):
        self.choice_flags.append(option["flag"])
        self.consequences.append(option["consequence"])
        self.elapsed += option.get("time_cost", 0)
        self.choice_points += option.get("points", 0)
        if option.get("final_decision"):
            self.final_decision = option["final_decision"]
        self.property_damage += option.get("property_damage", 0)
        self.toast = option["result"]
        self.toast_timer = 4.0
        if "mascot" in option:
            self.mascot.say(option["mascot"], 6)
        self.events.emit("choice_made", flag=option["flag"])

    # ---------- game flow ----------
    def game_over(self):
        self.game.state_manager.push(GameOver(self.game, self.retry))

    def retry(self):
        manager = self.game.state_manager
        manager.pop()                                     # close the top screen
        manager.change(BigMap(self.game, self.stage_id))  # restart the stage

    def build_stats(self):
        p = self.player
        time_s = int(self.play_time)
        total_damage = p.damage_taken
        all_quests = self.quests.all_done()
        objective_rate = self.quests.done_count() / max(1, len(self.quests.quests))
        item_rate = self.items_found / max(1, self.items_total)
        rescue_capacity = min(200, 100 * sum(1 for npc in self.npcs if npc.rescue_item))
        # Scores are composed from visible, comparable categories. Faster play
        # earns a modest bonus, while safety and decisions carry more weight.
        objective_points = round(400 * objective_rate)
        supply_points = round(200 * item_rate)
        prep_points = 100 if self.prep_choice == "community_radio" else 50
        decision_points = min(200, 100 + prep_points + min(100, max(0, self.choice_points)))
        response_points = max(0, round(100 - time_s * 0.35))
        safety_points = max(0, round(100 - total_damage * 0.8 - self.property_damage * 0.25))
        rescues = sum(1 for npc in self.npcs if npc.rescued)
        rescue_points = min(rescue_capacity, rescues * 100)
        score = objective_points + supply_points + decision_points + response_points + safety_points + rescue_points
        max_score = 1000 + rescue_capacity
        return {
            "stage_id": self.stage_id,
            "mission_number": self.game.session.STAGE_ORDER.index(self.stage_id) + 1,
            "mission_name": self.data.get("name", self.stage_id.replace("_", " ").title()),
            "chapter": self.data.get("chapter", "Campaign"),
            "time": time_s,
            "damage": total_damage,
            "property_damage": self.property_damage,
            "items_found": self.items_found,
            "items_total": self.items_total,
            "quests_done": self.quests.done_count(),
            "quests_total": len(self.quests.quests),
            "score": score,
            "max_score": max_score,
            "perfect": (p.damage_taken == 0 and self.property_damage == 0 and all_quests
                        and self.items_found == self.items_total),
            "rescues": sum(1 for npc in self.npcs if npc.rescued),
            "final_decision": self.final_decision,
            "score_breakdown": {
                "objectives": objective_points, "supplies": supply_points,
                "decisions": decision_points, "response": response_points,
                "safety": safety_points, "rescues": rescue_points,
            },
            "prep_choice": self.prep_choice,
            "difficulty": self.difficulty,
            "choices": self.choice_flags,
            "consequences": self.consequences,
            "choice_points": self.choice_points,
            "resources": sorted(self.inventory),
            "lessons": self.data.get("lessons", []),
            "story_clue": self.data.get("story_clue", "The community shares what it learned and prepares together."),
            "quiz": self.data.get("quiz", {}),
            "evacuated": self.evacuation_reached,
        }

    def show_results(self):
        stats = self.build_stats()
        self.game.session.complete_stage(self.stage_id)
        self.game.session.record_run(self.stage_id, stats)
        if self.stage_id == self.game.session.STAGE_ORDER[-1]:
            stats["ending"] = self.game.session.campaign_ending()
        self.game.state_manager.push(StageComplete(self.game, stats, self.retry))

    def handle_event(self, event):
        if self.map_open:
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_m):
                    self.map_open = False
                elif event.key == pygame.K_TAB:
                    self.map_page = "places" if self.map_page == "route" else "route"
            return
        if self.paused:
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_p):
                    self.paused = False
                elif event.key in (pygame.K_UP, pygame.K_w):
                    self.pause_selection = (self.pause_selection - 1) % len(self.pause_buttons)
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    self.pause_selection = (self.pause_selection + 1) % len(self.pause_buttons)
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self.activate_pause_option(self.pause_selection)
                elif event.key == pygame.K_r:
                    self.activate_pause_option(1)
                elif event.key == pygame.K_q:
                    self.activate_pause_option(2)
            elif event.type == pygame.MOUSEMOTION:
                pos = self.game.to_canvas_pos(event.pos)
                for index, rect in enumerate(self.pause_buttons):
                    if rect.collidepoint(pos):
                        self.pause_selection = index
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = self.game.to_canvas_pos(event.pos)
                for index, rect in enumerate(self.pause_buttons):
                    if rect.collidepoint(pos):
                        self.activate_pause_option(index)
            return
        if event.type != pygame.KEYDOWN:
            return
        if self.choice.active:
            self.choice.handle_key(event.key)
            return
        if self.dialogue.active:
            if event.key in (pygame.K_e, pygame.K_RETURN, pygame.K_SPACE, pygame.K_RCTRL):
                self.dialogue.advance()
                if not self.dialogue.active:
                    self.dialogue_npc = None
            return
        if event.key == pygame.K_ESCAPE:
            self.paused = True
            self.pause_selection = 0
        elif event.key == pygame.K_p:
            self.paused = True
            self.pause_selection = 0
        elif event.key == pygame.K_m:
            self.map_open = not self.map_open
        elif event.key == pygame.K_q:
            if self.player.activate_ability():
                self.toast = self.player.ability_notice
                self.toast_timer = self.player.ability_notice_time
        elif event.key in (pygame.K_e, pygame.K_RETURN, pygame.K_SPACE):
            npc = self.nearby_npc()
            if npc:
                self.talk(npc)
        elif event.key == pygame.K_h:
            self.mascot.ask_hint()
        elif event.key == pygame.K_TAB:
            self.show_all_quests = not self.show_all_quests

    def activate_pause_option(self, index):
        if index == 0:
            self.paused = False
        elif index == 1:
            self.game.state_manager.change(BigMap(self.game, self.stage_id))
        elif index == 2:
            self.game.state_manager.pop()

    def local_player_proxy(self):
        """Expose local cell coordinates to this scene's hazard simulation."""
        ox, oy = self.region_origin
        return SimpleNamespace(
            rect=self.player.rect.move(-ox, -oy),
            take_damage=self.player.take_damage,
        )

    # ---------- update ----------
    def update(self, dt):
        if self.paused:
            return
        self.dialogue.update(dt)
        if self.toast_timer > 0:
            self.toast_timer -= dt

        if self.finished:
            for npc in self.npcs:
                npc.update(dt, self.navigation_walls, self.island_geometry)
            self.finish_timer -= dt
            if self.finish_timer <= 0:
                self.show_results()
            return

        self.mascot.update(dt, self.player.rect)

        if self.dialogue.active or self.choice.active:
            return  # everything freezes while talking or choosing

        self.play_time += dt
        self.elapsed += dt
        for npc in self.npcs:
            if npc.following:
                refuge = next(iter(self.area_goals.values()))
                if refuge.colliderect(self.player.rect):
                    npc.evacuate(refuge, self.navigation_walls, (self.map_width, self.map_height),
                                 self.island_geometry)
                else:
                    npc.update_following(self.player.rect, dt, self.navigation_walls,
                                         self.island_geometry)
            npc.update(dt, self.navigation_walls, self.island_geometry)
            refuge = next(iter(self.area_goals.values()))
            if npc.following and refuge.colliderect(npc.rect):
                npc.following = False
                npc.evacuated = True
                npc.evacuation_path.clear()
            if npc.rescued and npc.evacuated:
                self.complete_rescue(npc)
        if self.evacuation_reached and self.try_finish_evacuation():
            return
        danger = self.danger()
        level, _ = self.level_of(danger)
        if level != self.last_level:
            self.last_level = level
            self.events.emit("danger_level", level=level)

        if self.rain:
            self.rain.update(dt, self.wind.push.x)
        local_player = self.local_player_proxy()
        inside_active_region = self.active_world_rect.colliderect(self.player.rect)
        if self.elapsed > self.start_delay and inside_active_region:
            if self.wind:
                self.wind.update(dt, danger)
            if self.debris:
                self.debris.update(dt, local_player, danger)

        if self.elapsed > self.start_delay and inside_active_region:
            self.disaster_system.update(
                dt, local_player, danger, self.local_safe_zones, self.events,
                quake_safe_zones=self.quake_safe_zones,
                protective_mask=bool({"mask", "respirator"} & self.inventory),
            )

        wind_push = self.wind.push if self.wind and inside_active_region else (0, 0)
        in_unsafe_water = inside_active_region and self.disaster_system.in_unsafe_water(
            local_player.rect, self.local_safe_zones
        )
        carry_scale = 0.76 if self.carried_npc else 1.0
        water_scale = 0.65 if in_unsafe_water else 1.0
        self.player.update(dt, self.navigation_walls, wind_push, carry_scale * water_scale,
                           collision=self.island_geometry)
        if self.carried_npc:
            self.carried_npc.rect.center = self.player.rect.center
            self.carried_npc.pos.update(self.player.rect.center)
        local_player = self.local_player_proxy()
        if inside_active_region and self.disaster_system.quake_active > 0 and any(
                zone.colliderect(local_player.rect) for zone in self.local_cover_spots):
            self.events.emit("cover_reached", hazard="earthquake")
        self.camera.follow(self.player.rect)
        if self.disaster_system.camera_shake:
            self.camera.offset.x += random.randint(-2, 2)
            self.camera.offset.y += random.randint(-2, 2)

        for item in self.items[:]:
            if self.player.rect.colliderect(item["rect"]):
                self.items.remove(item)
                self.events.emit("item_collected", item_id=item["id"])

        self.update_powerups(dt)

        for area in self.areas:
            goal = self.area_goals[area["id"]]
            if self.player.rect.colliderect(goal):
                self.events.emit("area_reached", area_id=area["id"])
                if self.carried_npc:
                    npc = self.carried_npc
                    npc.carried = False
                    npc.evacuated = True
                    npc.pos.update(goal.center)
                    npc.rect.center = goal.center
                    self.carried_npc = None
                    if npc.rescued:
                        self.complete_rescue(npc)
                if area["id"] in self.evacuation_area_ids:
                    first_arrival = not self.evacuation_reached
                    self.evacuation_reached = True
                    self.begin_evacuation()
                    if not self.try_finish_evacuation() and first_arrival:
                        npc = next((n for n in self.npcs
                                    if (n.rescued or n.id == self.required_evacuation_npc_id)
                                    and not n.evacuated), None)
                        name = npc.name if npc else "YOUR NEIGHBOR"
                        self.toast = f"WAIT FOR {name.upper()} TO REACH SAFETY"
                        self.toast_timer = 4.0
                    break

        if self.finished:
            return

        # Reaching the evacuation point ends the task phase immediately and
        # sends the whole community toward safety, even when optional tasks
        # remain. Mission-critical escorts still have to arrive before finish.
        if (self.quests.all_done() or self.evacuation_reached) and not self.evacuation_started:
            self.begin_evacuation()
            self.toast = "ALL NEIGHBORS: EVACUATE TO SAFETY"
            self.toast_timer = 4.0
        elif self.evacuation_started and self.evacuation_reached and self.evacuation_group_is_safe():
            self.try_finish_evacuation()
        elif self.evacuation_started and not self.evacuation_reached and self.evacuation_group_is_safe():
            if self.toast_timer <= 0:
                self.toast = "EVERYONE IS SAFE · YOU STILL NEED TO ARRIVE"
                self.toast_timer = 3.0
        elif self.player.health <= 0:
            self.game_over()

    def update_powerups(self, dt):
        if not self.powerups:
            self.powerup_timer -= dt
            if self.powerup_timer <= 0 and self.player.health < self.player.max_health - 8:
                self.spawn_health_powerup()
                self.powerup_timer = self.powerup_rng.uniform(18.0, 28.0)
            elif self.powerup_timer <= 0:
                self.powerup_timer = self.powerup_rng.uniform(7.0, 12.0)

        for pickup in self.powerups[:]:
            if self.player.rect.colliderect(pickup["rect"]):
                restored = min(25, self.player.max_health - self.player.health)
                self.player.health += restored
                self.powerups.remove(pickup)
                self.toast = f"FIRST AID PICKUP  +{restored} HP"
                self.toast_timer = 2.2

    def spawn_health_powerup(self):
        """Place a healing pickup on a short, clear path from the player."""
        candidates = []
        for radius in (48, 64, 80, 96):
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1),
                           (0.7, 0.7), (-0.7, 0.7), (0.7, -0.7), (-0.7, -0.7)):
                x = round(self.player.rect.centerx + radius * dx)
                y = round(self.player.rect.centery + radius * dy)
                rect = pygame.Rect(x - 4, y - 4, 8, 8)
                body = self.player.rect.copy()
                body.center = rect.center
                if (any(body.colliderect(wall) for wall in self.walls)
                        or self.island_geometry.is_blocked(body)):
                    continue
                if any(rect.colliderect(item["rect"]) for item in self.items):
                    continue
                if any(rect.colliderect(npc.rect.inflate(14, 14)) for npc in self.npcs):
                    continue
                if any(rect.colliderect(area["rect"]) for area in self.areas):
                    continue
                path_clear = True
                steps = max(1, int(radius / 4))
                for step in range(1, steps + 1):
                    t = step / steps
                    probe = self.player.rect.copy()
                    probe.center = (
                        round(self.player.rect.centerx + (x - self.player.rect.centerx) * t),
                        round(self.player.rect.centery + (y - self.player.rect.centery) * t),
                    )
                    if (any(probe.colliderect(wall) for wall in self.walls)
                            or self.island_geometry.is_blocked(probe)):
                        path_clear = False
                        break
                if path_clear:
                    candidates.append(rect)
        if candidates:
            self.powerups.append({"rect": self.powerup_rng.choice(candidates),
                                  "phase": self.powerup_rng.random() * 6.28})

    # ---------- draw ----------
    def draw(self, surface):
        surface.fill((18, 27, 34))
        cam = self.camera
        old_clip = surface.get_clip()
        surface.set_clip(cam.viewport)

        self.island_geometry.draw(surface, cam, self.route_data)
        for region, (region_art, origin, _wall_stage) in self.region_arts.items():
            region_rect = pygame.Rect(*origin, *CELL_SIZE)
            if not cam.apply(region_rect).colliderect(cam.viewport):
                continue
            region_camera = RegionCamera(cam, origin)
            region_art.draw_details(surface, region_camera)
            region_art.draw_landmarks(surface, region_camera)

        self.area_label_rects = []
        for area in self.areas:
            r = cam.apply(area["rect"])
            pygame.draw.rect(surface, tuple(area["color"]), r, 2)
            label = area["name"].upper()
            if r.colliderect(cam.viewport):
                label_size = self.font.size(label)
                label_x = max(cam.viewport.left + 3, min(
                    r.centerx - label_size[0] // 2,
                    cam.viewport.right - label_size[0] - 3,
                ))
                label_y = max(cam.viewport.top + 2, r.y - label_size[1] - 2)
                badge = pygame.Rect(label_x - 2, label_y - 1,
                                    label_size[0] + 4, label_size[1] + 2)
                self.area_label_rects.append(badge)
                pygame.draw.rect(surface, (13, 21, 31), badge)
                pygame.draw.rect(surface, tuple(area["color"]), badge, 1)
                theme.draw_text(surface, label, (label_x, label_y), "tiny",
                                theme.CREAM, shadow=True)

        for wall, wall_stage in self.region_wall_visuals:
            screen_wall = cam.apply(wall)
            if screen_wall.colliderect(cam.viewport):
                self.scene_art.draw_wall(surface, screen_wall, wall_stage)

        for item in self.items:
            draw_item(surface, cam.apply(item["rect"]), item["id"], item["color"],
                      item.get("name", ""))

        for pickup in self.powerups:
            rect = cam.apply(pickup["rect"])
            pulse = int((pygame.time.get_ticks() // 180) % 2)
            center = rect.center
            pygame.draw.circle(surface, (255, 228, 124), center, 7 + pulse, 1)
            heal = effect_frame("heal", (13, 13), pygame.time.get_ticks() / 1000)
            if heal:
                surface.blit(heal, heal.get_rect(center=center))
            else:
                pygame.draw.rect(surface, (245, 245, 220), (center[0] - 2, center[1] - 5, 4, 10))
                pygame.draw.rect(surface, (245, 245, 220), (center[0] - 5, center[1] - 2, 10, 4))

        for npc in self.npcs:
            npc.draw(surface, cam)

        local_camera = RegionCamera(cam, self.region_origin)
        if self.debris:
            self.debris.draw(surface, local_camera)
        self.disaster_system.draw_world(surface, local_camera)
        for zone in self.safe_zones:
            pygame.draw.rect(surface, (100, 240, 150), cam.apply(zone), 2)
        for cover in self.cover_spots:
            pygame.draw.rect(surface, (205, 244, 164), cam.apply(cover), 1)
        self.player.draw(surface, cam)
        if self.carried_npc:
            self.carried_npc.draw(surface, cam, carried_by=self.player)
        npc = self.nearby_npc()
        if npc and not self.dialogue.active and not self.choice.active and self.mascot.bubble_timer <= 0:
            r = cam.apply(npc.rect)
            tip = "E: TALK"
            tip_size = self.font.size(tip)
            content_width = tip_size[0] + 10
            tip_x = max(cam.viewport.left + 2, min(
                r.centerx - content_width // 2, cam.viewport.right - content_width - 2,
            ))
            tip_y = max(cam.viewport.top + 2, r.y - tip_size[1] - 3)
            badge = pygame.Rect(tip_x - 2, tip_y - 1, content_width + 4, tip_size[1] + 2)
            pygame.draw.rect(surface, (13, 21, 31), badge)
            pygame.draw.rect(surface, theme.HONEY, badge, 1)
            icon = effect_frame("interaction_icon", (8, 8), pygame.time.get_ticks() / 1000)
            if icon:
                surface.blit(icon, (tip_x, tip_y))
            theme.draw_text(surface, tip, (tip_x + (10 if icon else 0), tip_y), "tiny", theme.HONEY,
                            shadow=False)

        if self.rain:
            self.rain.draw(surface, cam.apply(self.player.rect).center)
        if self.wind:
            self.wind.draw(surface)
        self.disaster_system.draw_overlay(surface)

        if self.player.invuln > 0.7:   # red flash when hit
            flash = pygame.Surface(
                (settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT), pygame.SRCALPHA
            )
            flash.fill((255, 0, 0, 60))
            surface.blit(flash, (0, 0))

        surface.set_clip(old_clip)

        talking = self.dialogue.active or self.choice.active
        self.mascot.draw(surface, cam, show_bubble=False)
        self.draw_status(surface)
        self.draw_quest_hud(
            surface,
            notice=self.toast if self.toast_timer > 0 and not talking else None,
            expanded=not talking,
        )
        avoid_rects = [pygame.Rect(0, 0, 320, 21), self.quest_hud_rect,
                       pygame.Rect(0, 164, 320, 16), *self.area_label_rects]
        if not talking and not self.show_all_quests and not self.map_open:
            self.mascot.draw_bubble(surface, cam, avoid_rects)

        if self.dialogue.active:
            anchor = None
            if self.dialogue_npc:
                speaker_rect = cam.apply(self.dialogue_npc.rect)
                anchor = (speaker_rect.centerx, speaker_rect.top)
            self.dialogue.draw(surface, anchor, avoid_rects)
        self.choice.draw(surface)

        if self.paused:
            theme.TEXT_QUEUE.clear()
            shade = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            shade.fill((6, 10, 24, 190))
            surface.blit(shade, (0, 0))
            panel = pygame.Rect(52, 30, 216, 122)
            theme.draw_panel(surface, panel, title="PAUSED", accent=theme.HONEY)
            labels = ("RESUME STORY", "RESTART SCENE", "RETURN TO TITLE")
            for index, (rect, label) in enumerate(zip(self.pause_buttons, labels)):
                theme.draw_button(surface, rect, label, selected=index == self.pause_selection,
                                  font="tiny")
            theme.draw_text(surface, "UP/DOWN SELECT · ENTER OK · R RESTART · Q TITLE · ESC RESUME",
                            (160, 139), "tiny", theme.CREAM_DIM, anchor="center")
        elif self.map_open:
            self.draw_island_map(surface)

    def draw_status(self, surface):
        p = self.player
        pygame.draw.rect(surface, (13, 21, 31), (0, 0, 320, 21))
        pygame.draw.line(surface, (89, 111, 122), (0, 20), (319, 20))
        hp_color = theme.SAGE if p.health > p.max_health * 0.55 else theme.HONEY if p.health > p.max_health * 0.25 else theme.CORAL
        theme.draw_text(surface, f"HP {int(p.health):03d}", (5, 2), "tiny", theme.CREAM)
        theme.draw_bar(surface, (43, 4, 45, 7), p.health, p.max_health, hp_color)
        danger = self.danger()
        level, color = self.level_of(danger)
        theme.draw_text(surface, f"RISK {level}", (93, 2), "tiny", color)
        ability = "SPRINT" if p.ability == "sprint" else "FIRST AID"
        available = "READY" if p.ability_cooldown <= 0 else f"{p.ability_cooldown:.0f}s"
        theme.draw_text(surface, f"Q {ability} {available}", (170, 2), "tiny", theme.HONEY)
        if not self.choice.active:
            pygame.draw.rect(surface, (13, 21, 31), (0, 164, 320, 16))
            pygame.draw.line(surface, (89, 111, 122), (0, 164), (319, 164))
            evacuation_status = self.mission2_evacuation_status()
            if evacuation_status:
                theme.draw_text(surface, evacuation_status, (160, 167), "tiny",
                                theme.HONEY if "WAITING" in evacuation_status else theme.SAGE,
                                anchor="center")
            else:
                alert, alert_color = self.disaster_system.current_alert()
                controls = "MOVE  E TALK" if alert else "MOVE  E TALK  Q POWER  TAB TASKS  M MAP"
                theme.draw_text(surface, controls, (5, 167), "tiny", theme.CREAM_DIM)
                if alert:
                    theme.draw_text(surface, alert, (315, 167), "tiny", alert_color, anchor="topright")
                elif p.ability_notice_time > 0:
                    theme.draw_text(surface, p.ability_notice, (315, 167), "tiny", theme.HONEY,
                                    anchor="topright")

    def draw_island_map(self, surface):
        """Show the supplied island map with the campaign's next marked road."""
        # The overview replaces the field UI while open, so queued labels
        # cannot bleed through the modal.
        theme.TEXT_QUEUE.clear()
        current = self.player_map_stop()
        itinerary = self.route_data["campaign_route"]
        destination = self.story_map_destination(current)
        stop_ids, route_points = shortest_route(self.route_data, current, destination) \
            if destination else ([current], [self.route_data["stops"][current]["point"]])
        map_rect = pygame.Rect(0, 0, 185, 166)
        map_image = self.route_map_art.copy()
        source_w, source_h = map_image.get_size()
        # Keep the complete supplied map visible with its original proportions.
        map_width = round(map_rect.h * source_w / source_h)
        map_image = pygame.transform.scale(map_image, (map_width, map_rect.h))
        surface.blit(map_image, map_rect.topleft)

        for stop_id, color, radius in (
                (current, theme.SAGE, 2), (destination, theme.HONEY, 2)):
            if not stop_id:
                continue
            px, py = self.route_data["stops"][stop_id]["point"]
            # Offset the pin slightly from the printed place name so the map's
            # baked-in labels remain unobstructed at the smaller full-island fit.
            marker = (round(px * (map_width - 1)) + 5,
                      round(py * (map_rect.h - 1)) + 5)
            pygame.draw.circle(surface, (15, 24, 37), marker, radius + 4)
            pygame.draw.circle(surface, color, marker, radius + 2)
            pygame.draw.circle(surface, theme.CREAM, marker, radius + 2, 1)

        panel = pygame.Rect(188, 4, 128, 158)
        if self.map_page == "places":
            theme.draw_panel(surface, panel, title="ISLAND PLACES", accent=theme.HONEY,
                             alpha=250)
            ordered_ids = self.route_data.get("map_places", (
                "san_isidro", "nw_plateau", "santos", "harboro", "pulong",
                "lupa", "baybay", "bayani", "talon", "bukid", "pag_asa",
                "mount_talon",
            ))
            route_set = set(stop_ids)
            for index, stop_id in enumerate(ordered_ids):
                stop = self.route_data["stops"].get(stop_id)
                if not stop:
                    continue
                marker = "YOU" if stop_id == current else ">" if stop_id == destination else " "
                color = (theme.SAGE if stop_id == current else
                         theme.HONEY if stop_id == destination else
                         theme.CREAM if stop_id in route_set else theme.CREAM_DIM)
                row_y = 24 + index * 11
                theme.draw_text(surface, marker, (193, row_y), "tiny", color,
                                shadow=False)
                theme.draw_text(surface, stop["label"].upper(),
                                (206, row_y), "tiny", color, shadow=False)
        else:
            theme.draw_panel(surface, panel, title="STORY ROUTE", accent=theme.HONEY,
                             alpha=250)
            current_label = self.route_data["stops"][current]["label"]
            theme.draw_text(surface, "YOU ARE HERE", (193, 27), "tiny", theme.SAGE,
                            shadow=False)
            theme.draw_text(surface, current_label.upper(), (193, 38), "tiny", theme.CREAM,
                            shadow=False)
            if destination:
                destination_label = self.route_data["stops"][destination]["label"]
                theme.draw_text(surface, "NEXT CHAPTER", (193, 58), "tiny", theme.HONEY,
                                shadow=False)
                theme.draw_text(surface, destination_label.upper(), (193, 69), "tiny",
                                theme.CREAM, shadow=False)
            else:
                theme.draw_text(surface, "FINAL STOP", (193, 58), "tiny", theme.HONEY,
                                shadow=False)
                theme.draw_text(surface, "MOUNT TALON", (193, 69), "tiny", theme.CREAM,
                                shadow=False)
            theme.draw_text(surface, self.player_map_region().upper(), (193, 91), "tiny",
                            theme.CREAM_DIM, shadow=False)
            y = 101
            for index, stop_id in enumerate(itinerary):
                stop = self.route_data["stops"][stop_id]
                color = theme.SAGE if stop_id == current else theme.HONEY if stop_id == destination else theme.CREAM_DIM
                prefix = "●" if stop_id == current else "→" if stop_id == destination else "·"
                theme.draw_text(surface, f"{prefix} {stop['label'].upper()}",
                                (193, y + index * 9), "tiny", color, shadow=False)

        footer = "M CLOSE  ·  TAB " + ("ROUTE" if self.map_page == "places" else "PLACES")
        pygame.draw.rect(surface, (10, 20, 32), (0, 166, 320, 14))
        pygame.draw.line(surface, theme.HONEY, (0, 166), (319, 166), 1)
        theme.draw_text(surface, footer, (160, 168), "tiny", theme.CREAM_DIM, anchor="center")

    def story_map_destination(self, current):
        """Show the next marked story-route stop from the player's live location."""
        itinerary = self.route_data["campaign_route"]
        index = itinerary.index(current) if current in itinerary else -1
        return itinerary[index + 1] if 0 <= index < len(itinerary) - 1 else None

    def player_map_stop(self):
        """Return the nearest named campaign place from the map coordinates."""
        if self.stage_id == "final_shutdown":
            return "mount_talon"
        point = world_to_map(self.player.rect.center)
        route_ids = self.route_data["campaign_route"]
        return min(
            route_ids,
            key=lambda stop_id: sum(
                (point[axis] - self.route_data["stops"][stop_id]["point"][axis]
                 * MAP_SIZE[axis]) ** 2 for axis in (0, 1)
            ),
        )

    def player_map_region(self):
        """Return the island region the player is physically standing in."""
        if self.stage_id == "final_shutdown":
            return "Main Control Room"
        point = world_to_map(self.player.rect.center)
        return min(
            REGION_ANCHORS,
            key=lambda region: sum(
                (point[axis] - REGION_ANCHORS[region][axis]) ** 2
                for axis in (0, 1)
            ),
        )

    def draw_quest_hud(self, surface, notice=None, expanded=True):
        quests = self.quests.quests
        x, w = 164, 156
        self.quest_hud_rect = pygame.Rect(x, 0, w, 21)
        pending = [q for q in quests if not q["done"]]
        pygame.draw.line(surface, (67, 82, 95), (x, 11), (x, 19))
        count = f"TASK {self.quests.done_count()}/{len(quests)}  TAB"
        theme.draw_text(surface, count, (x + 5, 11), "tiny", theme.HONEY)
        current = None if notice else (pending[0] if pending else None)
        if notice:
            label = notice.upper()
            color = theme.HONEY
        elif self.carried_npc:
            label = f"CARRY {self.carried_npc.name.upper()} TO SAFETY"
            color = theme.HONEY
        elif self.evacuation_reached and self.required_evacuation_npc_id and not self.required_npc_is_safe():
            npc = next((n for n in self.npcs if n.id == self.required_evacuation_npc_id), None)
            name = npc.name.split()[-1].upper() if npc else "NEIGHBOR"
            label = f"WAIT: {name}"
            color = theme.HONEY
        elif current:
            label = self.quest_short_label(current)
            color = theme.CREAM
        else:
            label, color = "ALL TASKS COMPLETE", theme.SAGE
        max_chars = 12
        if len(label) > max_chars:
            label = label[:max_chars - 1].rstrip() + "…"
        theme.draw_text(surface, label, (x + 69, 11), "tiny", color)

        # A dialogue/choice occupies the lower playfield; keep the optional
        # task list hidden until it closes so the two overlays never cover each other.
        if self.show_all_quests and expanded:
            panel = pygame.Rect(166, 23, 150, min(132, 18 + len(quests) * 11))
            theme.draw_panel(surface, panel, title="MISSION TASKS", alpha=248)
            for i, q in enumerate(quests):
                y = panel.y + 19 + i * 11
                box = pygame.Rect(panel.x + 6, y + 1, 7, 7)
                if q["done"]:
                    pygame.draw.rect(surface, theme.SAGE, box)
                    pygame.draw.lines(surface, theme.NIGHT, False,
                                      [(box.x + 1, box.y + 3), (box.x + 2, box.y + 4), (box.x + 4, box.y + 1)])
                else:
                    pygame.draw.rect(surface, theme.CREAM_DIM, box, 1)
                color = theme.SAGE if q["done"] else theme.CREAM
                title = q["title"].upper()
                if len(title) > 22:
                    title = title[:21].rstrip() + "…"
                theme.draw_text(surface, title, (panel.x + 18, y - 1), "tiny", color)

    def quest_short_label(self, quest):
        if quest["type"] == "collect":
            title = quest["title"].upper()
            noun = title.split("COLLECT ", 1)[-1].split("FIND ", 1)[-1]
            for prefix in ("EMERGENCY ", "BATTERY ", "DRINKING ", "PROTECTIVE ", "SPARE "):
                noun = noun.replace(prefix, "")
            label = f"GET {noun}"
            if len(label) > 12:
                label = f"GET {noun.split()[-1]}"
            return label
        if quest["type"] == "talk":
            npc = next((person for person in self.npcs if person.id == quest["target"]), None)
            name = npc.name.split()[-1].upper() if npc else "NEIGHBOR"
            return f"TALK: {name}"
        if quest["type"] == "rescue":
            npc = next((person for person in self.npcs if person.id == quest["target"]), None)
            name = npc.name.split()[-1].upper() if npc else "NEIGHBOR"
            return f"RESCUE {name}"
        if quest["type"] == "cover":
            return "TAKE COVER"
        return "GO TO SAFETY"
