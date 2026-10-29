"""Procedural, map-aligned island terrain and walkability geometry.

All coordinates in this module are native pixels from the supplied Mount
Talon map. The artwork itself is not loaded here; it remains exclusive to the
M map screen.
"""

from __future__ import annotations

import pygame
import heapq
import itertools

from src.world.island_world import MAP_SCALE, MAP_SIZE, WORLD_SIZE, map_to_world
from src.entities.reference_art import scaled


COASTLINE = (
    (425, 274), (398, 286), (366, 283), (342, 299), (316, 293),
    (292, 310), (263, 307), (238, 326), (211, 329), (183, 351),
    (155, 358), (131, 382), (109, 404), (91, 433), (70, 458),
    (59, 490), (43, 520), (35, 555), (21, 590), (17, 628),
    (24, 663), (20, 696), (28, 732), (35, 766), (51, 799),
    (74, 826), (105, 845), (140, 862), (182, 873), (228, 880),
    (274, 879), (319, 872), (360, 868), (396, 866), (433, 875),
    (467, 887), (500, 909), (535, 925), (575, 931), (618, 925),
    (660, 931), (703, 938), (746, 940), (786, 934), (826, 936),
    (866, 928), (906, 922), (948, 927), (986, 922), (1024, 919),
    (1064, 923), (1103, 914), (1141, 910), (1176, 898), (1206, 881),
    (1237, 868), (1267, 848), (1285, 817), (1303, 785), (1314, 748),
    (1311, 707), (1317, 669), (1308, 632), (1310, 594), (1302, 555),
    (1294, 516), (1287, 477), (1278, 439), (1265, 404), (1249, 370),
    (1228, 341), (1205, 318), (1177, 300), (1145, 282), (1110, 270),
    (1072, 258), (1035, 249), (997, 242), (960, 233), (923, 224),
    (886, 214), (850, 202), (814, 193), (777, 185), (739, 178),
    (701, 169), (663, 164), (627, 160), (593, 168), (560, 171),
    (529, 181), (500, 193), (475, 210), (453, 228), (437, 249),
)

# Internal water is represented by its visible centerline and width. Bridge
# decks cut only the four user-approved openings back into the land mask.
RIVERS = (
    {
        "id": "west_channel",
        "points": ((365, 290), (364, 350), (362, 410), (361, 462),
                   (325, 501), (331, 557), (335, 620), (316, 724), (345, 770)),
        "width": 12,
    },
    {
        "id": "east_channel",
        "points": ((790, 342), (824, 350), (862, 370), (900, 383),
                   (918, 422), (943, 470), (979, 547), (967, 614),
                   (954, 688), (945, 785)),
        "width": 16,
    },
)

BRIDGES = (
    {"id": "crossing_1", "point": (325, 501), "size": (38, 20)},
    {"id": "crossing_2", "point": (316, 724), "size": (40, 22)},
    {"id": "crossing_3", "point": (979, 547), "size": (38, 22)},
    {"id": "crossing_4_baybay", "point": (945, 785), "size": (42, 24)},
)

# Named water zones inside the shore. These approximate the blue lagoon,
# eastern wetland, south/east cove, and scenery-only Pulong port in the map.
WATER_BASINS = {
    "harboro_lagoon": ((47, 664), (73, 637), (121, 624), (180, 630),
                       (229, 646), (267, 678), (270, 728), (250, 772),
                       (205, 803), (143, 811), (89, 795), (52, 767)),
    "talon_wetland": ((1015, 522), (1084, 520), (1154, 526), (1234, 535),
                      (1280, 560), (1289, 600), (1273, 634), (1225, 654),
                      (1160, 650), (1090, 641), (1032, 620), (1005, 579)),
    "baybay_cove": ((944, 817), (989, 798), (1040, 802), (1091, 822),
                    (1141, 836), (1200, 838), (1258, 816), (1282, 848),
                    (1240, 879), (1170, 894), (1095, 889), (1031, 870),
                    (978, 850)),
}

# This peninsula is drawn as a port town but remains scenery-only by decision.
PULONG_SCENERY = ((530, 766), (570, 759), (626, 765), (684, 760),
                 (742, 774), (789, 801), (817, 844), (803, 887),
                 (763, 914), (711, 922), (658, 912), (610, 902),
                 (564, 877), (535, 838))

# A dock is walkable where it visibly begins on solid land and reaches a
# waterfront platform. Pulong docks are deliberately omitted by the decision.
DOCKS = (
    ((280, 686), (249, 693), (226, 711), (198, 729), (181, 749), (193, 761)),
    ((1010, 795), (1032, 780), (1056, 769)),
    ((1111, 808), (1137, 793), (1160, 781)),
)


class IslandGeometry:
    """One source of truth for coast, rivers, bridges, and walkable land."""

    _nav_cache = {}
    _rect_mask_cache = {}

    def __init__(self):
        self.walkable_surface = pygame.Surface(MAP_SIZE, pygame.SRCALPHA, 32)
        self.walkable_surface.fill((0, 0, 0, 0))
        pygame.draw.polygon(self.walkable_surface, (255, 255, 255), COASTLINE)
        for river in RIVERS:
            pygame.draw.lines(self.walkable_surface, (0, 0, 0, 0), False,
                              river["points"], river["width"])
        for polygon in WATER_BASINS.values():
            pygame.draw.polygon(self.walkable_surface, (0, 0, 0, 0), polygon)
        pygame.draw.polygon(self.walkable_surface, (0, 0, 0, 0), PULONG_SCENERY)

        for bridge in BRIDGES:
            width, height = bridge["size"]
            center = bridge["point"]
            pygame.draw.rect(self.walkable_surface, (255, 255, 255),
                             pygame.Rect(0, 0, width, height).move(
                                 center[0] - width // 2, center[1] - height // 2))
        for dock in DOCKS:
            pygame.draw.lines(self.walkable_surface, (255, 255, 255), False,
                              dock, 24)
        self.walkable_mask = pygame.mask.from_surface(self.walkable_surface, 1)
        self._scenery_trees = self._build_scenery_trees()
        self.waterways = []
        for river in RIVERS:
            xs = [point[0] for point in river["points"]]
            ys = [point[1] for point in river["points"]]
            pad = river["width"] // 2
            self.waterways.append(pygame.Rect(min(xs) - pad, min(ys) - pad,
                                               max(xs) - min(xs) + 2 * pad,
                                               max(ys) - min(ys) + 2 * pad).scale_by(
                                                   MAP_SCALE))
        for polygon in WATER_BASINS.values():
            xs, ys = zip(*polygon)
            self.waterways.append(pygame.Rect(min(xs), min(ys),
                                               max(xs) - min(xs),
                                               max(ys) - min(ys)).scale_by(MAP_SCALE))
        self.bridge_rects = []
        for bridge in BRIDGES:
            x, y = bridge["point"]
            width, height = bridge["size"]
            self.bridge_rects.append(pygame.Rect(x - width // 2, y - height // 2,
                                                  width, height).scale_by(MAP_SCALE))
        self._terrain_surface = self._build_reference_terrain()
        self._scaled_terrain = {}

    def _build_scenery_trees(self):
        """Pick stable, land-only canopy points outside the town clearings."""
        import random

        rng = random.Random(71309)
        groves = (
            (38, 306, 350, 390, 35),       # San Isidro's wooded edge
            (275, 235, 414, 348, 22),      # northwest plateau
            (603, 224, 1020, 344, 38),     # central mountain forest
            (722, 346, 1002, 508, 24),     # Bukid and river headwaters
            (1000, 280, 1300, 361, 18),    # northern Bayani ridge
            (1000, 474, 1290, 531, 10),    # clearings between farms
        )
        clearings = (
            pygame.Rect(70, 392, 270, 150), pygame.Rect(365, 528, 336, 188),
            pygame.Rect(1040, 360, 248, 154), pygame.Rect(512, 380, 104, 103),
            pygame.Rect(660, 153, 244, 162),
        )
        trees = []
        for left, top, right, bottom, count in groves:
            accepted = 0
            attempts = 0
            while accepted < count and attempts < count * 12:
                attempts += 1
                x, y = rng.randrange(left, right), rng.randrange(top, bottom)
                if not self.walkable_mask.get_at((x, y)):
                    continue
                if any(clear.collidepoint(x, y) for clear in clearings):
                    continue
                trees.append((x, y, rng.randrange(7, 12),
                              rng.choice(((41, 102, 58), (49, 120, 62),
                                          (67, 139, 69), (81, 148, 70)))))
                accepted += 1
        return tuple(trees)

    def _build_reference_terrain(self):
        """Paint a continuous, colorful pixel landscape inside the approved coast."""
        import random

        rng = random.Random(24831)
        sea = pygame.Surface(MAP_SIZE)
        sea.fill((18, 132, 204))
        # Small scattered wave marks add texture without a repeating tile grid.
        for _ in range(2100):
            x, y = rng.randrange(MAP_SIZE[0]), rng.randrange(MAP_SIZE[1])
            color = ((49, 168, 220) if rng.randrange(3)
                     else (94, 199, 226))
            length = rng.randrange(3, 10)
            pygame.draw.line(sea, color, (x, y), (x + length, y), 1)
            if rng.randrange(4) == 0:
                pygame.draw.line(sea, (12, 111, 182), (x + 1, y + 2),
                                 (x + length - 1, y + 2), 1)

        land = pygame.Surface(MAP_SIZE, pygame.SRCALPHA)
        land.fill((100, 177, 82, 255))
        # Biome masses follow the approved map anchors, blended with softer
        # irregular edges so the island reads as terrain rather than blocks.
        pygame.draw.polygon(land, (64, 148, 75),
                            ((42, 478), (55, 414), (111, 359), (174, 337),
                             (254, 347), (313, 397), (334, 459), (300, 516),
                             (222, 548), (134, 535), (71, 512)))
        pygame.draw.polygon(land, (174, 159, 82),
                            ((347, 554), (394, 504), (476, 488), (564, 504),
                             (642, 549), (702, 627), (676, 698), (601, 743),
                             (501, 748), (420, 709), (366, 648)))
        pygame.draw.polygon(land, (126, 169, 75),
                            ((1015, 321), (1086, 296), (1174, 306), (1241, 353),
                             (1282, 415), (1275, 478), (1220, 522), (1130, 535),
                             (1055, 495), (1014, 427)))
        pygame.draw.polygon(land, (116, 113, 88),
                            ((396, 354), (435, 315), (486, 294), (548, 318),
                             (584, 371), (564, 430), (516, 470), (454, 463), (411, 418)))
        pygame.draw.ellipse(land, (73, 69, 58), (435, 356, 110, 91))
        pygame.draw.ellipse(land, (218, 97, 41), (448, 370, 83, 61), 5)
        pygame.draw.ellipse(land, (250, 160, 54), (469, 386, 46, 30), 3)

        mountain_ridges = (
            ((240, 333), (292, 278), (331, 301), (367, 257), (414, 318), (442, 349)),
            ((610, 252), (659, 194), (698, 221), (745, 174), (789, 228), (830, 250)),
            ((810, 266), (855, 211), (893, 239), (933, 190), (981, 255), (1018, 291)),
        )
        for ridge in mountain_ridges:
            pygame.draw.polygon(land, (97, 105, 86), ridge)
            highlight = [(x, y) for x, y in ridge[1:4]]
            pygame.draw.lines(land, (190, 172, 128), False, highlight, 3)
            pygame.draw.lines(land, (69, 113, 73), False, ridge[3:], 4)

        # Rice plots and grove clearings are drawn as short, broken contours.
        for y, left, right in ((355, 1041, 1225), (382, 1035, 1248),
                               (414, 1045, 1260), (449, 1054, 1261),
                               (575, 397, 670), (606, 411, 682),
                               (638, 430, 669), (674, 450, 643)):
            for x in range(left, right, 28):
                end = min(right, x + rng.randrange(12, 25))
                pygame.draw.line(land, (218, 195, 113), (x, y), (end, y + 2), 2)
                pygame.draw.line(land, (118, 153, 75), (x + 3, y + 4), (end, y + 5), 1)

        # Irregular vegetation speckles preserve broad, readable ground color.
        # Layered paths make the geography readable while leaving the actual
        # collision mask authoritative. They are painted first, then clipped
        # to land below so no decoration creates a false crossing.
        for path in (
                ((80, 472), (138, 453), (205, 465), (263, 443), (301, 407)),
                ((375, 566), (431, 551), (487, 578), (548, 564), (613, 594)),
                ((1032, 402), (1091, 421), (1154, 404), (1229, 435)),
                ((643, 313), (712, 338), (763, 365), (841, 399), (901, 453)),
                ((345, 781), (419, 800), (495, 831), (535, 882))):
            pygame.draw.lines(land, (155, 133, 88), False, path, 7)
            pygame.draw.lines(land, (207, 185, 129), False, path, 3)

        for _ in range(6800):
            x, y = rng.randrange(MAP_SIZE[0]), rng.randrange(MAP_SIZE[1])
            if 390 < x < 610 and 292 < y < 485:
                color = rng.choice(((89, 85, 71), (147, 122, 83), (178, 147, 87), (204, 150, 72)))
            elif (x < 350 and 305 < y < 560) or (x > 740 and y < 530):
                color = rng.choice(((50, 130, 62), (75, 157, 69), (105, 176, 77), (132, 185, 82)))
            elif ((340 < x < 740 and y > 490) or (990 < x < 1290 and y < 540)):
                color = rng.choice(((179, 159, 79), (212, 185, 92), (131, 165, 77), (226, 190, 102)))
            else:
                color = rng.choice(((73, 153, 71), (102, 184, 79), (125, 191, 89), (146, 196, 100)))
            if rng.randrange(3):
                length = rng.randrange(2, 6)
                pygame.draw.line(land, color, (x, y), (x + length, y - 1), 1)
            else:
                pygame.draw.rect(land, color, (x, y, 2, rng.choice((2, 3))))

        # Low canopy clusters make the forest districts read as dense groves.
        for _ in range(1150):
            x, y = rng.randrange(MAP_SIZE[0]), rng.randrange(MAP_SIZE[1])
            in_forest = ((x < 360 and 300 < y < 565)
                         or (x > 720 and y < 548)
                         or (320 < x < 410 and 270 < y < 355))
            if not in_forest:
                continue
            shade = rng.choice(((40, 119, 57), (52, 140, 62), (70, 157, 69)))
            radius = rng.randrange(5, 10)
            pygame.draw.circle(land, shade, (x, y), radius)
            pygame.draw.circle(land, shade, (x + radius // 2, y + radius // 3),
                               max(2, radius * 2 // 3))
            pygame.draw.circle(land, (min(255, shade[0] + 33),
                                      min(255, shade[1] + 42),
                                      min(255, shade[2] + 18)),
                               (x - radius // 3, y - radius // 3), max(1, radius // 3))

        # A few small rocky outcrops give the highlands and volcano a silhouette.
        for x, y, radius in ((445, 333, 15), (482, 306, 12), (552, 326, 15),
                             (572, 425, 11), (420, 414, 10), (340, 304, 8)):
            pygame.draw.polygon(land, (96, 92, 77),
                                ((x - radius, y + radius // 3), (x - radius // 3, y - radius),
                                 (x + radius // 2, y - radius // 2), (x + radius, y + radius // 3)))
            pygame.draw.line(land, (184, 157, 111), (x - radius // 3, y - radius),
                             (x, y + radius // 3), 2)

        mask_surface = self.walkable_mask.to_surface(
            setcolor=(255, 255, 255, 255), unsetcolor=(0, 0, 0, 0))
        land.blit(mask_surface, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        sea.blit(land, (0, 0))
        # Sand fringe and a bright waterline give the irregular coast depth.
        coast = pygame.Surface(MAP_SIZE, pygame.SRCALPHA)
        pygame.draw.lines(coast, (232, 197, 127, 235), True, COASTLINE, 7)
        pygame.draw.lines(coast, (255, 225, 158, 235), True, COASTLINE, 2)
        coast.blit(mask_surface, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        sea.blit(coast, (0, 0))
        return sea

    def _draw_reference_terrain(self, surface, camera):
        if self._terrain_surface is None:
            return False
        z = MAP_SCALE * camera.zoom
        size = (max(1, round(MAP_SIZE[0] * z)), max(1, round(MAP_SIZE[1] * z)))
        terrain = self._scaled_terrain.get(size)
        if terrain is None:
            terrain = pygame.transform.scale(self._terrain_surface, size)
            self._scaled_terrain = {size: terrain}
        position = (camera.viewport.x - round(camera.offset.x * camera.zoom),
                    camera.viewport.y - round(camera.offset.y * camera.zoom))
        surface.blit(terrain, position)
        return True

    @staticmethod
    def _map_rect(world_rect):
        rect = pygame.Rect(world_rect)
        left = rect.left // MAP_SCALE
        top = rect.top // MAP_SCALE
        right = (rect.right + MAP_SCALE - 1) // MAP_SCALE
        bottom = (rect.bottom + MAP_SCALE - 1) // MAP_SCALE
        return pygame.Rect(left, top, max(1, right - left), max(1, bottom - top))

    def is_walkable_point(self, world_point):
        mx = int(world_point[0] // MAP_SCALE)
        my = int(world_point[1] // MAP_SCALE)
        return (0 <= mx < MAP_SIZE[0] and 0 <= my < MAP_SIZE[1]
                and bool(self.walkable_mask.get_at((mx, my))))

    def is_blocked(self, world_rect):
        """Return True if any part of a world-space actor is in water."""
        rect = pygame.Rect(world_rect)
        map_rect = self._map_rect(rect)
        if (map_rect.left < 0 or map_rect.top < 0
                or map_rect.right > MAP_SIZE[0] or map_rect.bottom > MAP_SIZE[1]):
            return True
        size = map_rect.size
        rect_mask = self._rect_mask_cache.get(size)
        if rect_mask is None:
            rect_mask = pygame.mask.Mask(size, fill=True)
            self._rect_mask_cache[size] = rect_mask
        return self.walkable_mask.overlap_area(rect_mask, map_rect.topleft) != size[0] * size[1]

    def find_path(self, start, goal_rect, walls=(), actor_size=(12, 12),
                  cell_size=12):
        """Find a land-only path to a rectangle; return world-space waypoints.

        The grid is lazily rasterized once per actor size. Water and coastline
        are therefore identical for players, followers and evacuation routes.
        Stage walls are added per search, and bridges are traversable because
        they are already part of the walkable mask.
        """
        cols = (WORLD_SIZE[0] + cell_size - 1) // cell_size
        rows = (WORLD_SIZE[1] + cell_size - 1) // cell_size
        actor_w, actor_h = actor_size
        cache = self._nav_cache.get((cell_size, tuple(actor_size), WORLD_SIZE))
        if cache is None:
            walkable = set()
            for gy in range(rows):
                cy = gy * cell_size + cell_size // 2
                for gx in range(cols):
                    cx = gx * cell_size + cell_size // 2
                    rect = pygame.Rect(cx - actor_w // 2, cy - actor_h // 2,
                                       actor_w, actor_h)
                    if not self.is_blocked(rect):
                        walkable.add((gx, gy))
            cache = (cols, rows, walkable)
            self._nav_cache[(cell_size, tuple(actor_size), WORLD_SIZE)] = cache
        _, _, walkable = cache
        goal_rect = pygame.Rect(goal_rect)

        # Limit obstacle rasterization to cells overlapped by each wall.
        blocked = set()
        half_w, half_h = actor_w // 2, actor_h // 2
        for wall in walls:
            left = max(0, (wall.left - half_w) // cell_size)
            right = min(cols, (wall.right + half_w + cell_size - 1) // cell_size)
            top = max(0, (wall.top - half_h) // cell_size)
            bottom = min(rows, (wall.bottom + half_h + cell_size - 1) // cell_size)
            for gy in range(top, bottom):
                cy = gy * cell_size + cell_size // 2
                for gx in range(left, right):
                    cx = gx * cell_size + cell_size // 2
                    if pygame.Rect(cx - half_w, cy - half_h, actor_w,
                                   actor_h).colliderect(wall):
                        blocked.add((gx, gy))

        def nearest_nodes(point, limit=5):
            gx0 = max(0, min(cols - 1, round((point[0] - cell_size / 2) / cell_size)))
            gy0 = max(0, min(rows - 1, round((point[1] - cell_size / 2) / cell_size)))
            candidates = []
            for radius in range(limit + 1):
                for gy in range(max(0, gy0 - radius), min(rows, gy0 + radius + 1)):
                    for gx in range(max(0, gx0 - radius), min(cols, gx0 + radius + 1)):
                        node = (gx, gy)
                        if node in walkable and node not in blocked:
                            cx = gx * cell_size + cell_size // 2
                            cy = gy * cell_size + cell_size // 2
                            distance = (cx - point[0]) ** 2 + (cy - point[1]) ** 2
                            candidates.append((distance, node))
                if candidates:
                    return [node for _, node in sorted(candidates)]
            return []

        starts = nearest_nodes(start)
        if not starts:
            return []
        # An evacuation building may have walls around its perimeter. Any
        # navigable cell whose actor body reaches the interior goal is valid.
        gx0 = max(0, (goal_rect.left - half_w) // cell_size)
        gx1 = min(cols, (goal_rect.right + half_w + cell_size - 1) // cell_size)
        gy0 = max(0, (goal_rect.top - half_h) // cell_size)
        gy1 = min(rows, (goal_rect.bottom + half_h + cell_size - 1) // cell_size)
        goals = set()
        for gy in range(gy0, gy1):
            cy = gy * cell_size + cell_size // 2
            for gx in range(gx0, gx1):
                node = (gx, gy)
                if node not in walkable or node in blocked:
                    continue
                body = pygame.Rect(gx * cell_size + cell_size // 2 - half_w,
                                   cy - half_h, actor_w, actor_h)
                if body.colliderect(goal_rect):
                    goals.add(node)
        if not goals:
            return []

        goal_left = min(gx for gx, _gy in goals)
        goal_right = max(gx for gx, _gy in goals)
        goal_top = min(gy for _gx, gy in goals)
        goal_bottom = max(gy for _gx, gy in goals)

        def heuristic(node):
            x, y = node
            dx = goal_left - x if x < goal_left else x - goal_right if x > goal_right else 0
            dy = goal_top - y if y < goal_top else y - goal_bottom if y > goal_bottom else 0
            return dx + dy

        # A* avoids searching the full island for nearby objects, while still
        # allowing long detours through the approved bridge corridors.
        sequence = itertools.count()
        frontier = []
        parents = {}
        costs = {}
        for node in starts:
            costs[node] = 0
            parents[node] = None
            heapq.heappush(frontier, (heuristic(node), next(sequence), node))
        found = None
        directions = ((1, 0), (-1, 0), (0, 1), (0, -1))
        while frontier:
            _priority, _order, current = heapq.heappop(frontier)
            if current in goals:
                found = current
                break
            next_cost = costs[current] + 1
            for dx, dy in directions:
                neighbor = (current[0] + dx, current[1] + dy)
                if (neighbor in costs or neighbor in blocked
                        or neighbor not in walkable):
                    continue
                costs[neighbor] = next_cost
                parents[neighbor] = current
                heapq.heappush(frontier, (next_cost + heuristic(neighbor),
                                          next(sequence), neighbor))
        if found is None:
            return []
        path = []
        while found is not None:
            path.append(pygame.Vector2(found[0] * cell_size + cell_size // 2,
                                       found[1] * cell_size + cell_size // 2))
            found = parents[found]
        path.reverse()
        return path[1:]

    @staticmethod
    def _screen_points(points, camera):
        result = []
        for point in points:
            wx, wy = map_to_world(point)
            result.append((
                camera.viewport.x + round((wx - camera.offset.x) * camera.zoom),
                camera.viewport.y + round((wy - camera.offset.y) * camera.zoom),
            ))
        return result

    @staticmethod
    def _map_polygon(surface, camera, points, color, outline=None, width=1):
        screen = IslandGeometry._screen_points(points, camera)
        pygame.draw.polygon(surface, color, screen)
        if outline:
            pygame.draw.lines(surface, outline, True, screen,
                              max(1, round(width * MAP_SCALE * camera.zoom)))

    @staticmethod
    def _tree(surface, camera, x, y, size=9, color=(49, 104, 60)):
        cx, cy = IslandGeometry._screen_points(((x, y),), camera)[0]
        z = MAP_SCALE * camera.zoom
        radius = max(3, round(size * .62 * z))
        pygame.draw.ellipse(surface, (45, 99, 60),
                            (cx - radius, cy - radius // 2, radius * 2, radius))
        pygame.draw.rect(surface, (99, 70, 43),
                         (cx - max(1, round(z)), cy - 1, max(2, round(z * 2)),
                          max(3, round(size * .55 * z))))
        foliage = (color[0], color[1], color[2])
        bright = (min(255, color[0] + 35), min(255, color[1] + 48),
                  min(255, color[2] + 18))
        deep = (max(0, color[0] - 20), max(0, color[1] - 25), max(0, color[2] - 12))
        pygame.draw.circle(surface, deep, (cx, cy - radius // 2), radius)
        pygame.draw.circle(surface, foliage, (cx - radius // 2, cy - radius // 2),
                           max(2, radius * 2 // 3))
        pygame.draw.circle(surface, bright, (cx + radius // 3, cy - radius),
                           max(2, radius // 2))
        pygame.draw.rect(surface, (177, 205, 113),
                         (cx - radius // 3, cy - radius, max(2, radius // 2),
                          max(1, round(z))))

    @staticmethod
    def _house(surface, camera, x, y, body=(221, 191, 131), roof=(151, 80, 48)):
        z = MAP_SCALE * camera.zoom
        variants = (1, 2, 7, 8)
        building_index = variants[((x * 31 + y * 19) // 11) % len(variants)]
        source = scaled("buildings", f"building_{building_index:02}",
                        # Coordinates for placement are map-scaled, but sprite
                        # dimensions are already expressed in world pixels.
                        # Applying MAP_SCALE here again made houses twice as
                        # large as their intended world footprint.
                        (round(40 * camera.zoom), round(32 * camera.zoom)))
        if source:
            anchor = IslandGeometry._screen_points(((x + 10, y + 15),), camera)[0]
            surface.blit(source, source.get_rect(midbottom=anchor))
            return
        # Map buildings are deliberately broader than a person sprite so the
        # scale reads as a walkable settlement, not toy-sized structures.
        corners = ((x, y), (x + 20, y), (x + 20, y + 14), (x, y + 14))
        IslandGeometry._map_polygon(surface, camera, corners, body, (70, 56, 42), 1)
        roof_points = IslandGeometry._screen_points(
            ((x - 3, y), (x + 10, y - 8), (x + 23, y)), camera)
        pygame.draw.polygon(surface, roof, roof_points)
        door = IslandGeometry._screen_points(((x + 8, y + 8),), camera)[0]
        z = MAP_SCALE * camera.zoom
        door_size = max(3, round(4 * z))
        pygame.draw.rect(surface, (78, 57, 41), (door[0], door[1], door_size, round(6 * z)))
        for wx in (x + 3, x + 14):
            window = IslandGeometry._screen_points(((wx, y + 4),), camera)[0]
            window_size = max(2, round(3 * z))
            pygame.draw.rect(surface, (118, 177, 177), (*window, window_size, window_size))
            pygame.draw.rect(surface, (242, 222, 176), (*window, window_size, window_size), 1)

    @staticmethod
    def _landmark_building(surface, camera, x, y, kind, width=25, height=18):
        """Draw a large, recognizable guide establishment in the island world."""
        z = MAP_SCALE * camera.zoom
        art_index = {"school": 3, "clinic": 5, "market": 7, "farmhouse": 8,
                     "lighthouse": 10, "research": 14, "control": 14}.get(kind)
        if art_index is not None:
            asset = scaled("buildings", f"building_{art_index:02}",
                           # width/height are map-space footprints; z converts
                           # each to world pixels and applies camera zoom once.
                           (round(max(width, 24) * z),
                            round(max(height, 22) * z)))
            if asset:
                anchor = IslandGeometry._screen_points(((x + width // 2,
                                                         y + height),), camera)[0]
                surface.blit(asset, asset.get_rect(midbottom=anchor))
                return
        if kind == "lighthouse":
            screen = IslandGeometry._screen_points(
                ((x, y), (x + 13, y + 27)), camera)
            rect = pygame.Rect(screen[0], (screen[1][0] - screen[0][0],
                                           screen[1][1] - screen[0][1]))
            pygame.draw.ellipse(surface, (37, 68, 60), rect.inflate(8, 3).move(0, 2))
            pygame.draw.rect(surface, (226, 216, 177), rect)
            pygame.draw.rect(surface, (85, 77, 66), rect, max(1, round(z)))
            band_y = rect.y + rect.h // 2
            pygame.draw.rect(surface, (192, 63, 52), (rect.x, band_y, rect.w, max(2, round(3 * z))))
            pygame.draw.rect(surface, (78, 83, 80), (rect.x - 2, rect.y - 4,
                                                      rect.w + 4, max(4, round(4 * z))))
            pygame.draw.rect(surface, (250, 223, 126),
                             (rect.centerx - 2, rect.y + 2, max(3, round(4 * z)), max(3, round(4 * z))))
            return

        palette = {
            "school": ((221, 198, 144), (54, 104, 139), (236, 207, 111)),
            "clinic": ((221, 213, 177), (70, 130, 126), (218, 83, 68)),
            "market": ((214, 185, 127), (135, 76, 50), (240, 194, 98)),
            "farmhouse": ((195, 164, 109), (116, 76, 46), (229, 204, 126)),
            "research": ((158, 179, 168), (63, 80, 83), (89, 206, 213)),
            "control": ((119, 132, 133), (46, 57, 68), (95, 221, 202)),
        }
        wall, roof, accent = palette[kind]
        corners = IslandGeometry._screen_points(
            ((x, y), (x + width, y), (x + width, y + height), (x, y + height)), camera)
        left, top = corners[0]
        right, bottom = corners[2]
        rect = pygame.Rect(left, top, right - left, bottom - top)
        pygame.draw.ellipse(surface, (38, 66, 54), rect.inflate(8, 4).move(0, 2))
        pygame.draw.rect(surface, wall, rect)
        pygame.draw.rect(surface, (64, 57, 48), rect, max(1, round(z)))

        roof_points = IslandGeometry._screen_points(
            ((x - 3, y + 1), (x + width // 2, y - 8), (x + width + 3, y + 1)), camera)
        pygame.draw.polygon(surface, roof, roof_points)
        pygame.draw.lines(surface, (48, 48, 45), False, roof_points, max(1, round(z)))

        door_width = max(3, round(4 * z))
        door_height = max(6, round(7 * z))
        pygame.draw.rect(surface, (71, 54, 43),
                         (rect.centerx - door_width // 2, rect.bottom - door_height,
                          door_width, door_height))
        for wx in (rect.x + round(5 * z), rect.right - round(8 * z)):
            window = pygame.Rect(wx, rect.y + round(5 * z), max(3, round(4 * z)),
                                 max(3, round(4 * z)))
            pygame.draw.rect(surface, (106, 174, 182), window)
            pygame.draw.rect(surface, (243, 226, 182), window, 1)

        if kind in ("school", "clinic"):
            sign = pygame.Rect(rect.centerx - round(5 * z), rect.y - round(5 * z),
                               max(8, round(10 * z)), max(5, round(6 * z)))
            pygame.draw.rect(surface, (247, 237, 204), sign)
            pygame.draw.rect(surface, accent, sign, 1)
            if kind == "clinic":
                pygame.draw.rect(surface, accent, (sign.centerx - 1, sign.y + 1, 2, sign.h - 2))
                pygame.draw.rect(surface, accent, (sign.x + 2, sign.centery - 1, sign.w - 4, 2))
            else:
                pygame.draw.line(surface, accent, sign.midleft, sign.midright, 1)
        elif kind in ("research", "control"):
            panel = pygame.Rect(rect.centerx - round(3 * z), rect.y + round(2 * z),
                                max(5, round(6 * z)), max(4, round(5 * z)))
            pygame.draw.rect(surface, (24, 48, 54), panel)
            pygame.draw.rect(surface, accent, panel.inflate(-2, -2))

    def draw(self, surface, camera, route_data=None):
        """Draw clean, unlabeled terrain aligned with the supplied map geography."""
        viewport = camera.viewport
        has_reference_terrain = self._draw_reference_terrain(surface, camera)
        if not has_reference_terrain:
            pygame.draw.rect(surface, (44, 137, 181), viewport)
            self._map_polygon(surface, camera, COASTLINE, (83, 143, 88),
                              (44, 91, 69), 2)
        else:
            shore = self._screen_points(COASTLINE, camera)
            pygame.draw.lines(surface, (227, 199, 126), True, shore,
                              max(2, round(4 * MAP_SCALE * camera.zoom)))
            pygame.draw.lines(surface, (51, 116, 75), True, shore,
                              max(1, round(MAP_SCALE * camera.zoom)))

        # Distinct terrain regions: west forest/home, central farmland/town,
        # northeast terraces, the Pag-Asa volcanic basin, and coastal wetlands.
        if not has_reference_terrain:
            self._map_polygon(surface, camera,
                          ((60, 430), (105, 365), (225, 330), (310, 350),
                           (346, 427), (325, 505), (248, 545), (134, 525),
                           (61, 493)), (61, 125, 76), (92, 151, 85), 2)
            self._map_polygon(surface, camera,
                          ((365, 520), (457, 485), (565, 520), (638, 582),
                           (704, 654), (647, 728), (545, 746), (443, 698),
                           (385, 630)), (171, 147, 79), (205, 177, 102), 2)
            self._map_polygon(surface, camera,
                          ((1020, 322), (1108, 286), (1208, 324), (1274, 392),
                           (1284, 482), (1202, 517), (1101, 500), (1044, 444)),
                          (78, 139, 78), (111, 163, 91), 2)
            self._map_polygon(surface, camera,
                          ((403, 337), (450, 300), (515, 300), (566, 337),
                           (579, 397), (544, 454), (485, 481), (427, 450),
                           (397, 394)), (107, 78, 54), (205, 112, 44), 3)

        # Simple terraces and contour bands add readable regional character.
        if not has_reference_terrain:
            for y, left, right in ((364, 1050, 1228), (392, 1038, 1240),
                               (424, 1050, 1250), (455, 1060, 1264),
                               (594, 398, 680), (625, 418, 681),
                               (658, 432, 655), (690, 462, 631)):
                a = self._screen_points(((left, y), (right, y + 3)), camera)
                pygame.draw.line(surface, (182, 173, 118), a[0], a[1],
                                 max(1, round(2 * MAP_SCALE * camera.zoom)))

        # Pixel-art tree clusters and houses are positioned in map geography,
        # so each district has a recognizable silhouette instead of blank tiles.
        forest_trees = (
            (83, 420), (104, 391), (128, 433), (151, 402), (173, 448),
            (198, 412), (226, 445), (255, 405), (281, 444), (305, 471),
            (82, 482), (116, 501), (154, 478), (193, 507), (233, 488),
            (277, 510), (1054, 362), (1082, 338), (1110, 377), (1142, 344),
            (1172, 382), (1204, 355), (1232, 410), (1060, 453), (1101, 475),
            (1147, 449), (1192, 485), (1230, 462), (335, 318), (364, 305),
            (603, 360), (634, 386), (680, 371), (735, 380), (763, 406),
            (867, 446), (905, 429), (930, 460), (1024, 488),
        )
        for index, (x, y) in enumerate(forest_trees):
            color = ((48, 103, 58), (60, 121, 66), (75, 137, 72))[index % 3]
            self._tree(surface, camera, x, y, 8 + index % 4, color)

        houses = (
            (112, 441), (146, 470), (179, 462), (218, 450), (239, 438), (273, 474),
            (397, 570), (425, 600), (459, 552), (484, 628), (516, 573), (550, 650),
            (570, 607), (425, 650), (600, 671), (648, 642), (1080, 396),
            (1100, 454), (1127, 421), (1180, 395), (1210, 451), (1154, 483),
            (823, 620), (868, 659), (923, 628), (1056, 724), (1092, 766),
            (1120, 749), (1201, 740),
        )
        for index, (x, y) in enumerate(houses):
            roof = (150, 76, 49) if index % 2 == 0 else (178, 104, 56)
            self._house(surface, camera, x, y, roof=roof)

        # Named public buildings make the guide's island landmarks readable
        # while roaming, with one visual identity per region.
        for kind, x, y, width, height in (
                ("school", 158, 421, 25, 18),
                ("clinic", 446, 601, 23, 17),
                ("market", 548, 632, 25, 18),
                ("lighthouse", 28, 699, 13, 27),
                ("farmhouse", 1150, 451, 23, 17),
                ("research", 535, 402, 27, 19),
                ("control", 776, 209, 30, 21)):
            self._landmark_building(surface, camera, x, y, kind, width, height)

        # Rocky ridges and ash patches distinguish the volcanic valley.
        for x, y, radius in ((443, 333, 12), (478, 309, 9), (553, 329, 13),
                             (566, 432, 10), (421, 424, 8)):
            center = self._screen_points(((x, y),), camera)[0]
            r = max(2, round(radius * MAP_SCALE * camera.zoom))
            pygame.draw.polygon(surface, (111, 95, 75),
                                ((center[0] - r, center[1] + r // 2),
                                 (center[0] - r // 3, center[1] - r),
                                 (center[0] + r, center[1] + r // 2)))
            pygame.draw.line(surface, (172, 143, 103),
                             (center[0] - r // 3, center[1] - r),
                             (center[0], center[1] + r // 2), max(1, round(camera.zoom)))

        # The caldera is scenery artwork; the supplied labeled map is not used.
        crater = self._screen_points(((448, 355), (547, 355), (547, 451), (448, 451)), camera)
        pygame.draw.ellipse(surface, (61, 48, 42), pygame.Rect(crater[0],
                         (crater[2][0] - crater[0][0], crater[2][1] - crater[0][1])))
        crater_rect = pygame.Rect(crater[0], (crater[2][0] - crater[0][0], crater[2][1] - crater[0][1]))
        pygame.draw.ellipse(surface, (220, 93, 37), crater_rect.inflate(-12, -12),
                            max(1, round(5 * MAP_SCALE * camera.zoom)))

        if route_data:
            for edge in route_data.get("connections", ()):
                points = [tuple(point) for point in edge.get("path", ())]
                if len(points) < 2:
                    continue
                native = [(round(x * MAP_SIZE[0]), round(y * MAP_SIZE[1]))
                          for x, y in points]
                screen_points = self._screen_points(native, camera)
                pygame.draw.lines(surface, (135, 111, 75), False, screen_points,
                                  max(1, round(3 * MAP_SCALE * camera.zoom)))

        # Blue water covers any route line not explicitly bridged. Decks are
        # drawn after the water so only accepted crossings look traversable.
        water_color = (35, 119, 158)
        for river in RIVERS:
            points = self._screen_points(river["points"], camera)
            pygame.draw.lines(surface, water_color, False, points,
                              max(1, round(river["width"] * MAP_SCALE * camera.zoom)))
            pygame.draw.lines(surface, (93, 179, 195), False, points,
                              max(1, round(2 * MAP_SCALE * camera.zoom)))
        for name, polygon in WATER_BASINS.items():
            color = (73, 130, 145) if name == "talon_wetland" else (39, 126, 164)
            self._map_polygon(surface, camera, polygon, color, (89, 171, 190), 1)

        # Actual canopy silhouettes make forest edges and the NW uplands read
        # as places, without turning decoration into collision geometry.
        for x, y, size, color in self._scenery_trees:
            self._tree(surface, camera, x, y, size, color)

        self._map_polygon(surface, camera, PULONG_SCENERY, (48, 149, 180), (93, 192, 210), 2)
        for x, y in ((593, 814), (626, 842), (664, 805), (700, 853),
                     (735, 817), (755, 860), (680, 883), (610, 872)):
            anchor = self._screen_points(((x + 11, y + 17),), camera)[0]
            house = scaled("buildings", "building_09", (round(29 * camera.zoom),
                                                           round(24 * camera.zoom)))
            if house:
                pygame.draw.line(surface, (82, 82, 68), anchor,
                                 (anchor[0], anchor[1] + max(3, round(8 * camera.zoom))),
                                 max(1, round(2 * camera.zoom)))
                surface.blit(house, house.get_rect(midbottom=anchor))
        # Decorative Pulong pier is intentionally absent from DOCKS/collision.
        pier = self._screen_points(((740, 878), (758, 908), (777, 946), (780, 981)), camera)
        pygame.draw.lines(surface, (73, 53, 42), False, pier,
                          max(2, round(8 * MAP_SCALE * camera.zoom)))
        pygame.draw.lines(surface, (174, 130, 78), False, pier,
                          max(1, round(2 * MAP_SCALE * camera.zoom)))

        for dock in DOCKS:
            points = self._screen_points(dock, camera)
            width = max(2, round(7 * MAP_SCALE * camera.zoom))
            pygame.draw.lines(surface, (95, 64, 42), False, points, width)
            pygame.draw.lines(surface, (174, 130, 78), False, points,
                              max(1, round(2 * MAP_SCALE * camera.zoom)))

        for bridge in BRIDGES:
            x, y = bridge["point"]
            width, height = bridge["size"]
            rect = pygame.Rect(x - width // 2, y - height // 2, width, height)
            a, b = self._screen_points((rect.topleft, rect.bottomright), camera)
            screen_rect = pygame.Rect(a, (b[0] - a[0], b[1] - a[1]))
            bridge_art = scaled("buildings", "building_19",
                                (max(screen_rect.w, 43), max(screen_rect.h, 25)))
            if bridge_art:
                surface.blit(bridge_art, bridge_art.get_rect(center=screen_rect.center))
            else:
                pygame.draw.rect(surface, (85, 57, 39), screen_rect)
                pygame.draw.rect(surface, (196, 148, 87), screen_rect, 1)
