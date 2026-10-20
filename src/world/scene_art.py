"""Procedural pixel-art scenery used when a stage has no painted background."""
import random

import pygame

from src.ui.pixel_art import grass_tiles
from src.entities.reference_art import scaled, sprite
from src.ui import theme


class SceneArt:
    GROUND_PALETTES = {
        "typhoon": ((111, 177, 88), (73, 144, 73), (158, 195, 105)),
        "flood": ((91, 165, 143), (59, 131, 128), (126, 188, 156)),
        "earthquake": ((157, 157, 103), (119, 130, 85), (190, 181, 119)),
        "volcano": ((135, 126, 91), (97, 94, 76), (179, 145, 91)),
        "wildfire": ((188, 160, 82), (146, 129, 69), (217, 183, 97)),
        "typhoon_flood": ((91, 157, 131), (64, 127, 113), (133, 184, 143)),
        "typhoon_flood_earthquake": ((128, 154, 103), (93, 126, 84), (166, 179, 112)),
        "volcano_wildfire": ((158, 132, 76), (119, 106, 64), (203, 159, 81)),
        "flood_earthquake_volcano": ((129, 148, 112), (93, 122, 94), (170, 170, 123)),
        "typhoon_flood_tsunami": ((77, 145, 150), (49, 117, 130), (113, 176, 167)),
        "typhoon_flood_earthquake_tsunami": ((89, 139, 143), (61, 111, 121), (126, 165, 155)),
        "all_hazards_final": ((113, 151, 102), (79, 120, 84), (150, 177, 112)),
    }

    def __init__(self, stage, stage_id):
        self.width, self.height = stage["map_size"]
        self.chapter = stage.get("chapter", "")
        seed = sum((index + 1) * ord(char) for index, char in enumerate(stage_id))
        self.rng = random.Random(seed)
        hazards = set(stage.get("hazards", {}).get("disasters", ()))
        palette = stage.get("ground_palette") or self.GROUND_PALETTES.get(stage_id)
        if palette is None:
            if "volcano" in hazards or "landslide" in hazards:
                palette = ((124, 119, 101), (91, 88, 80), (157, 143, 111))
            elif "flash_fire" in hazards or "wildfire" in hazards:
                palette = ((151, 142, 92), (116, 113, 72), (184, 160, 99))
            elif "flood" in hazards or "tsunami" in hazards:
                palette = ((82, 137, 128), (59, 109, 105), (117, 164, 141))
            elif "earthquake" in hazards:
                palette = ((138, 135, 107), (107, 111, 87), (166, 156, 115))
            else:
                palette = ((107, 148, 105), (75, 119, 85), (139, 172, 112))
        self.tiles = grass_tiles(8, 16, seed, palette)
        self.earthquake = "earthquake" in hazards
        self.volcanic = "volcano" in hazards
        self.wildfire = "wildfire" in hazards or "flash_fire" in hazards
        self.flood = "flood" in hazards or "tsunami" in hazards
        if "Harbor" in self.chapter:
            ground_kind = "beach"
        elif "Central Town" in self.chapter:
            ground_kind = "farmland"
        elif "North West Plateau" in self.chapter:
            ground_kind = "mountain"
        elif "North East Plains" in self.chapter:
            ground_kind = "farmland"
        elif "Volcano Valley" in self.chapter or self.volcanic:
            ground_kind = "rocky"
        elif self.chapter == "Home Village":
            ground_kind = "forest"
        elif self.flood:
            ground_kind = "beach"
        else:
            ground_kind = "grass"
        # Actual clean terrain tiles from the supplied pack; collision and
        # hazard detail remain authored by the existing stage data.
        self.reference_ground = scaled("terrain", ground_kind, (16, 16))
        self.ground_tile_size = 16
        self.location_background = (sprite("locations", "control_room")
                                    if stage_id == "final_shutdown" else None)
        self.zoom_tiles = {}
        self.areas = [
            {**area, "rect": pygame.Rect(*area["rect"])}
            for area in stage.get("areas", [])
        ]
        self.shelter_colliders = []
        for area in self.areas:
            if self._is_building(area["name"]):
                self.shelter_colliders.extend(self._building_collision(area["rect"]))

        self.cover_spots = []
        if self.earthquake:
            for safe_zone in stage.get("safe_zones", []):
                zone = pygame.Rect(*safe_zone)
                # Objective shelters already have a structure. Open safe fields
                # get a visible sturdy table that players can move underneath.
                if not any(zone.colliderect(area["rect"]) for area in self.areas):
                    size = (min(44, zone.w - 12), min(24, zone.h - 16))
                    cover = pygame.Rect(0, 0, *size)
                    cover.center = zone.center
                    self.cover_spots.append(cover)

        reserved = [pygame.Rect(*area["rect"]).inflate(22, 22) for area in stage.get("areas", [])]
        reserved += [spot.inflate(14, 14) for spot in self.cover_spots]
        reserved += [pygame.Rect(*npc["pos"], 12, 12).inflate(20, 20) for npc in stage.get("npcs", [])]
        reserved += [pygame.Rect(*item["pos"], 8, 8).inflate(18, 18) for item in stage.get("items", [])]
        start = stage.get("player_start", (0, 0))
        reserved.append(pygame.Rect(start[0] - 20, start[1] - 20, 52, 52))
        obstacles = [pygame.Rect(*wall) for wall in stage.get("walls", [])]

        self.details = []
        self.details_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        kinds = ["grass", "flower", "stone", "grass", "crack" if self.earthquake else "shrub"]
        if self.volcanic:
            kinds += ["ash", "rock"]
        if self.wildfire:
            kinds += ["char", "ash"]
        if self.flood:
            kinds += ["reed", "stone"]
        for _ in range(58):
            x = self.rng.randrange(16, self.width - 16)
            y = self.rng.randrange(18, self.height - 16)
            rect = pygame.Rect(x - 5, y - 5, 10, 10)
            if any(rect.colliderect(zone) for zone in reserved + obstacles):
                continue
            self.details.append((x, y, self.rng.choice(kinds), self.rng.randrange(3)))
        self._build_details_surface()

    def draw_ground(self, surface, camera):
        if self.location_background:
            size = (max(1, round(self.width * camera.zoom)),
                    max(1, round(self.height * camera.zoom)))
            key = ("control_room", *size)
            background = self.zoom_tiles.get(key)
            if background is None:
                background = pygame.transform.scale(self.location_background, size)
                self.zoom_tiles[key] = background
            position = (camera.viewport.x - round(camera.offset.x * camera.zoom),
                        camera.viewport.y - round(camera.offset.y * camera.zoom))
            surface.blit(background, position)
            return
        shift_x = round(camera.offset.x * camera.zoom)
        shift_y = round(camera.offset.y * camera.zoom)
        tile_size = self.ground_tile_size
        left = max(0, int(camera.offset.x) // tile_size)
        top = max(0, int(camera.offset.y) // tile_size)
        right = min((self.width + tile_size - 1) // tile_size,
                    left + int(camera.viewport.w / (tile_size * camera.zoom)) + 3)
        bottom = min((self.height + tile_size - 1) // tile_size,
                     top + int(camera.viewport.h / (tile_size * camera.zoom)) + 3)
        for row in range(top, bottom):
            for col in range(left, right):
                tile_index = (col * 7 + row * 11) % len(self.tiles)
                tile = self.reference_ground or self.tiles[tile_index]
                wx0, wy0 = col * tile_size, row * tile_size
                wx1, wy1 = min(self.width, wx0 + tile_size), min(self.height, wy0 + tile_size)
                x0 = camera.viewport.x + round(wx0 * camera.zoom) - shift_x
                y0 = camera.viewport.y + round(wy0 * camera.zoom) - shift_y
                x1 = camera.viewport.x + round(wx1 * camera.zoom) - shift_x
                y1 = camera.viewport.y + round(wy1 * camera.zoom) - shift_y
                x, y = x0, y0
                size = (max(1, x1 - x0), max(1, y1 - y0))
                # Cache by the visual tile actually being drawn. Using only
                # the procedural tile index let unrelated terrain variants
                # reuse each other's scaled surfaces and appear to overlap.
                cache_key = ("reference" if self.reference_ground else tile_index, *size)
                if cache_key not in self.zoom_tiles:
                    self.zoom_tiles[cache_key] = pygame.transform.scale(tile, size)
                tile = self.zoom_tiles[cache_key]
                surface.blit(tile, (x, y))
        self.draw_region_terrain(surface, camera)

    def draw_region_terrain(self, surface, camera):
        """Give each campaign region its own readable ground landmarks."""
        z = camera.zoom
        def point(x, y):
            return (camera.viewport.x + round((x - camera.offset.x) * z),
                    camera.viewport.y + round((y - camera.offset.y) * z))
        def line(color, a, b, width=1):
            pygame.draw.line(surface, color, point(*a), point(*b), max(1, round(width * z)))

        if "Harbor" in self.chapter:
            # Pier planks and a small boat silhouette establish the coastal town.
            for y in (46, 54, 62):
                line((104, 91, 66), (28, y), (205, y), 2)
            for x in range(42, 205, 20):
                line((77, 66, 53), (x, 45), (x, 64), 1)
            boat = [point(112, 35), point(161, 35), point(151, 44), point(124, 44)]
            pygame.draw.polygon(surface, (103, 69, 51), boat)
            line((224, 216, 174), (137, 20), (137, 34), 1)
        elif "Central Town" in self.chapter:
            # A paved crossing and painted lane marks distinguish town maps.
            road = camera.apply(pygame.Rect(0, 168, self.width, 30))
            pygame.draw.rect(surface, (116, 119, 105), road)
            pygame.draw.line(surface, (194, 185, 141), road.midtop, road.midbottom, 1)
            for x in range(24, self.width, 54):
                mark = camera.apply(pygame.Rect(x, 181, 20, 2))
                pygame.draw.rect(surface, (223, 209, 158), mark)
        elif "North East Plains" in self.chapter:
            # Contour lines suggest rice terraces and shallow irrigation beds.
            for y, inset in ((42, 18), (68, 32), (94, 12), (220, 28), (246, 8), (272, 24)):
                line((166, 165, 105), (inset, y), (self.width - inset, y), 2)
                line((84, 122, 76), (inset + 14, y + 4), (self.width - inset - 16, y + 4), 1)
        elif "Volcano Valley" in self.chapter or self.chapter == "Finale":
            # Distant volcanic ridges; the nearer rock route is built from stage walls.
            ridges = [point(375, 106), point(454, 18), point(520, 106),
                      point(563, 61), point(632, 112)]
            pygame.draw.polygon(surface, (83, 80, 70), ridges)
            pygame.draw.lines(surface, (151, 116, 78), False, ridges[:3], max(1, round(2 * z)))
            line((57, 89, 73), (0, 295), (self.width, 295), 2)
        elif "North West Plateau" in self.chapter:
            # Layered hillside contours and rock shelves make the plateau distinct.
            for y, inset in ((40, 30), (62, 56), (250, 36), (275, 64)):
                line((107, 118, 82), (inset, y), (self.width - inset, y + 10), 2)
                line((185, 159, 103), (inset + 10, y + 4), (self.width - inset - 15, y + 14), 1)
        else:
            # Home-community footpaths around the first shelter.
            line((177, 151, 105), (35, 295), (220, 245), 3)
            line((177, 151, 105), (220, 245), (330, 150), 3)

    @staticmethod
    def draw_wall(surface, rect, stage_id="typhoon"):
        if rect.width <= 0 or rect.height <= 0:
            return
        if rect.width >= 600 or rect.height >= 320:
            edge = (70, 66, 63) if "volcano" in stage_id or "earthquake" in stage_id else (54, 91, 91) if "flood" in stage_id else (54, 83, 59)
            pygame.draw.rect(surface, edge, rect)
            pygame.draw.line(surface, (185, 167, 128), rect.topleft, rect.topright, 2)
            pygame.draw.line(surface, (28, 34, 35), rect.bottomleft, rect.bottomright, 2)
            return
        if rect.w < 1 or rect.h < 1:
            return
        pygame.draw.ellipse(surface, (24, 32, 29), rect.inflate(5, 5))
        if "volcano" in stage_id:
            points = [(rect.left, rect.bottom - 1),
                      (rect.left + rect.w // 6, rect.top + rect.h // 2),
                      (rect.left + rect.w // 3, rect.top + rect.h // 3),
                      (rect.centerx, rect.top),
                      (rect.right - rect.w // 4, rect.top + rect.h // 3),
                      (rect.right, rect.bottom - 1)]
            pygame.draw.polygon(surface, (52, 48, 49), points)
            pygame.draw.lines(surface, (128, 103, 84), False, points[1:5], 2)
            pygame.draw.line(surface, (255, 116, 48), (rect.centerx, rect.centery),
                             (rect.centerx + max(2, rect.w // 5), rect.bottom - 2), 1)
            pygame.draw.circle(surface, (235, 101, 48), (rect.right - 3, rect.top + 3), 1)
            return
        if "wildfire" in stage_id or "flash_fire" in stage_id or "facility_fire" in stage_id:
            horizontal = rect.w >= rect.h
            count = max(1, min(3, rect.h // 6 if horizontal else rect.w // 6))
            for layer in range(count):
                log = rect.inflate(-2, -2)
                if horizontal:
                    log.y += layer * 4
                    log.h = max(3, rect.h // max(1, count))
                else:
                    log.x += layer * 4
                    log.w = max(3, rect.w // max(1, count))
                pygame.draw.rect(surface, (49, 39, 34), log)
                pygame.draw.line(surface, (126, 71, 43), log.topleft, log.bottomright, 2)
                pygame.draw.line(surface, (86, 54, 41), log.bottomleft, log.topright, 1)
            pygame.draw.circle(surface, (244, 113, 44), (rect.centerx, rect.top + 1), 1)
            return
        if "flood" in stage_id or "tsunami" in stage_id:
            pygame.draw.rect(surface, (79, 62, 49), rect)
            horizontal = rect.w >= rect.h
            spacing = 10
            if horizontal:
                for x in range(rect.left + 2, rect.right - 3, spacing):
                    yy = rect.top + (2 if ((x - rect.left) // spacing) % 2 else max(2, rect.h // 2))
                    bag = pygame.Rect(x, yy, min(12, rect.right - x), max(4, rect.h // 2))
                    pygame.draw.ellipse(surface, (145, 116, 78), bag)
                    pygame.draw.arc(surface, (204, 171, 121), bag.inflate(-2, -2), 0, 3.14, 1)
            else:
                for y in range(rect.top + 2, rect.bottom - 3, spacing):
                    bag = pygame.Rect(rect.left + 2, y, max(4, rect.w - 4), min(12, rect.bottom - y))
                    pygame.draw.ellipse(surface, (145, 116, 78), bag)
                    pygame.draw.arc(surface, (204, 171, 121), bag.inflate(-2, -2), 0, 3.14, 1)
            pygame.draw.line(surface, (93, 168, 183), rect.topleft, rect.topright, 1)
            return
        if "earthquake" in stage_id:
            pygame.draw.rect(surface, (85, 77, 73), rect)
            pygame.draw.line(surface, (172, 145, 122), rect.topleft, rect.topright, 2)
            brick_h = max(5, rect.h // 3)
            for row, y in enumerate(range(rect.top + brick_h, rect.bottom, brick_h)):
                pygame.draw.line(surface, (48, 46, 46), (rect.left, y), (rect.right - 1, y), 1)
                offset = brick_h if row % 2 else brick_h // 2
                for x in range(rect.left + offset, rect.right, max(7, brick_h * 2)):
                    pygame.draw.line(surface, (48, 46, 46), (x, y - brick_h), (x, y), 1)
            if rect.w > 14 and rect.h > 8:
                pygame.draw.lines(surface, (43, 39, 39), False,
                                  [(rect.centerx, rect.top), (rect.centerx - 2, rect.centery),
                                   (rect.centerx + 1, rect.bottom - 1)], 1)
            return
        if "landslide" in stage_id:
            pygame.draw.ellipse(surface, (76, 62, 51), rect)
            pygame.draw.ellipse(surface, (151, 119, 85), rect.inflate(-4, -4), 1)
            pygame.draw.line(surface, (80, 66, 58), rect.midtop, rect.midbottom, 1)
            return
        # Typhoon debris: recognizable split planks, supports and nail heads.
        pygame.draw.rect(surface, (82, 55, 39), rect)
        pygame.draw.line(surface, (182, 130, 78), (rect.left + 1, rect.top + 2),
                         (rect.right - 2, rect.top + 2), 2)
        pygame.draw.line(surface, (50, 39, 33), (rect.left + 2, rect.bottom - 2),
                         (rect.right - 1, rect.bottom - 2), 2)
        pygame.draw.line(surface, (138, 90, 53), rect.topleft, rect.bottomright, 2)
        pygame.draw.line(surface, (56, 43, 36), rect.topright, rect.bottomleft, 2)
        for point in (rect.midtop, rect.midbottom):
            pygame.draw.circle(surface, (232, 195, 137), point, 1)

    @staticmethod
    def _is_building(name):
        name = name.lower()
        return any(word in name for word in ("shelter", "center", "centre", "school"))

    @staticmethod
    def _building_collision(rect):
        """Solid shelter walls with a clear, player-sized entrance."""
        width = max(26, rect.w - 12)
        height = max(24, rect.h - 18)
        left = rect.centerx - width // 2
        top = rect.centery - height // 2 - 2
        # Keep the entrance comfortably wider than the 12px player/NPC collider.
        door_width = 24
        front_y = top + height - 6
        side_width = 5
        return [
            pygame.Rect(left, top, width, side_width),
            pygame.Rect(left, top, side_width, height),
            pygame.Rect(left + width - side_width, top, side_width, height),
            pygame.Rect(left, front_y, (width - door_width) // 2, side_width),
            pygame.Rect(left + (width + door_width) // 2, front_y,
                        (width - door_width) // 2, side_width),
        ]

    @staticmethod
    def building_interior(rect):
        """Walkable goal/safe rectangle inside the illustrated building."""
        width = max(16, rect.w - 28)
        height = max(16, rect.h - 42)
        inner = pygame.Rect(0, 0, width, height)
        inner.centerx = rect.centerx
        inner.bottom = rect.bottom - 7
        return inner

    def objective_rect(self, area):
        rect = area["rect"]
        return self.building_interior(rect) if self._is_building(area["name"]) else rect

    @staticmethod
    def draw_shelter(surface, rect):
        """Draw a shelter large enough to read as the objective landmark."""
        building_name = "building_06" if rect.w > 52 else "building_17"
        art = scaled("buildings", building_name,
                     (max(46, round(rect.w * 0.8)),
                      max(42, round(rect.h * 0.8))))
        if art:
            surface.blit(art, art.get_rect(midbottom=(rect.centerx, rect.bottom + 4)))
            return
        if rect.w < 34 or rect.h < 34:
            return
        width = rect.w - 10
        height = rect.h - 12
        cx = rect.centerx
        base_y = rect.bottom - 6
        left = cx - width // 2
        roof_h = max(10, height // 3)
        body_h = height - roof_h
        body = pygame.Rect(left + 4, base_y - body_h, width - 8, body_h)

        pygame.draw.ellipse(surface, (44, 78, 53), (left - 3, base_y - 1, width + 6, 8))
        pygame.draw.rect(surface, (207, 190, 151), body)
        pygame.draw.rect(surface, (115, 91, 73), body, 2)
        pygame.draw.polygon(surface, (122, 72, 57),
                            [(left - 2, body.top + 1), (cx, body.top - roof_h),
                             (left + width + 2, body.top + 1)])
        pygame.draw.line(surface, (190, 125, 83), (left, body.top),
                         (cx, body.top - roof_h + 2), 2)
        pygame.draw.line(surface, (190, 125, 83), (cx, body.top - roof_h + 2),
                         (left + width, body.top), 2)

        door_w = 12
        door_h = min(body.h - 3, max(12, body.h - 4))
        door = pygame.Rect(cx - door_w // 2, base_y - door_h, door_w, door_h)
        pygame.draw.rect(surface, (76, 58, 52), door)
        pygame.draw.rect(surface, (41, 48, 45), door, 1)
        pygame.draw.circle(surface, (239, 202, 113), (door.right - 3, door.centery), 1)

        window_w = max(5, min(9, (width - door_w - 12) // 2))
        window_y = body.top + max(3, body.h // 3)
        for wx in (left + 8, left + width - window_w - 8):
            window = pygame.Rect(wx, window_y, window_w, 8)
            pygame.draw.rect(surface, (107, 164, 166), window)
            pygame.draw.rect(surface, (244, 225, 180), window, 1)
            pygame.draw.line(surface, (244, 225, 180), (window.centerx, window.y),
                             (window.centerx, window.bottom), 1)

        sign = pygame.Rect(cx - 7, body.top - 5, 14, 8)
        pygame.draw.rect(surface, (224, 243, 210), sign)
        pygame.draw.rect(surface, (56, 142, 91), sign, 1)
        pygame.draw.line(surface, (56, 142, 91), (cx, sign.y + 1),
                         (cx, sign.bottom - 1), 2)
        pygame.draw.line(surface, (56, 142, 91), (cx - 3, sign.centery),
                         (cx + 3, sign.centery), 2)

    @staticmethod
    def draw_high_ground(surface, rect):
        if rect.w < 30 or rect.h < 30:
            return
        mound = pygame.Rect(rect.x + 8, rect.y + 18, rect.w - 16, rect.h - 25)
        pygame.draw.ellipse(surface, (67, 120, 76), mound)
        pygame.draw.ellipse(surface, (114, 163, 94), mound.inflate(-8, -7))
        pygame.draw.line(surface, (208, 185, 124), (rect.x + 7, rect.bottom - 8),
                         (rect.centerx, rect.centery), 3)
        pygame.draw.rect(surface, (241, 235, 198),
                         (rect.centerx - 9, rect.y + 5, 18, 11))
        pygame.draw.rect(surface, (67, 139, 97),
                         (rect.centerx - 9, rect.y + 5, 18, 11), 1)
        pygame.draw.line(surface, (67, 139, 97), (rect.centerx, rect.y + 7),
                         (rect.centerx, rect.y + 14), 2)
        pygame.draw.line(surface, (67, 139, 97), (rect.centerx - 3, rect.y + 10),
                         (rect.centerx + 3, rect.y + 10), 2)

    @staticmethod
    def draw_assembly_point(surface, rect):
        if rect.w < 30 or rect.h < 30:
            return
        cx, cy = rect.center
        pygame.draw.ellipse(surface, (52, 102, 68), (cx - 19, cy + 7, 38, 9))
        pygame.draw.circle(surface, (115, 177, 103), (cx, cy + 5), 15)
        pygame.draw.circle(surface, (193, 221, 150), (cx, cy + 5), 10, 1)
        pygame.draw.line(surface, (94, 72, 54), (cx + 12, cy - 15),
                         (cx + 12, cy + 8), 2)
        pygame.draw.polygon(surface, (244, 220, 129),
                            [(cx + 13, cy - 14), (cx + 25, cy - 11), (cx + 13, cy - 7)])

    def draw_landmarks(self, surface, camera):
        for area in self.areas:
            rect = camera.apply(area["rect"])
            name = area["name"].lower()
            if self._is_building(name):
                self.draw_shelter(surface, rect)
            elif "high ground" in name or name == "high ground":
                self.draw_high_ground(surface, rect)
            else:
                self.draw_assembly_point(surface, rect)

        for cover in self.cover_spots:
            rect = camera.apply(cover)
            cx, cy = rect.center
            pygame.draw.ellipse(surface, (48, 82, 58), (cx - 23, cy + 7, 46, 8))
            # Sturdy tabletop with open space beneath: the safe position is
            # physically obvious and the player can move under its center.
            pygame.draw.rect(surface, (111, 69, 45), (cx - 21, cy - 7, 42, 5))
            pygame.draw.rect(surface, (175, 125, 77), (cx - 23, cy - 10, 46, 5))
            pygame.draw.rect(surface, (89, 57, 40), (cx - 19, cy - 5, 4, 17))
            pygame.draw.rect(surface, (89, 57, 40), (cx + 15, cy - 5, 4, 17))
            pygame.draw.rect(surface, (73, 139, 94), (cx - 24, cy - 17, 48, 5))
            pygame.draw.rect(surface, (231, 244, 206), (cx - 24, cy - 17, 48, 5), 1)
            pygame.draw.line(surface, (73, 139, 94), (cx - 18, cy - 15),
                             (cx + 18, cy - 15), 1)
            viewport = camera.viewport
            if rect.colliderect(viewport):
                label = "SAFE COVER: GET UNDER TABLE"
                font = theme.get_font("tiny")
                text_w, text_h = font.size(label)
                label_x = max(viewport.left + 2, min(cx - text_w // 2,
                                                     viewport.right - text_w - 2))
                label_y = max(viewport.top + 2, min(rect.y - 3 - text_h,
                                                    viewport.bottom - text_h - 2))
                theme.draw_text(surface, label, (label_x, label_y), "tiny",
                                (255, 249, 222), shadow=True)

    def draw_chapter_establishment(self, surface, camera):
        """Paint one large guide-appropriate establishment for the chapter intro."""
        chapter = self.chapter.lower()
        if "home village" in chapter:
            kind, wall, roof, sign = "HOUSE", (210, 187, 140), (157, 77, 50), (236, 209, 124)
        elif "north west" in chapter:
            kind, wall, roof, sign = "FIELD SHELTER", (174, 164, 133), (92, 79, 67), (238, 189, 80)
        elif "central town" in chapter:
            kind, wall, roof, sign = "CLINIC", (214, 216, 190), (63, 112, 133), (211, 75, 66)
        elif "harbor" in chapter:
            kind, wall, roof, sign = "HARBOR OFFICE", (221, 200, 150), (48, 108, 139), (239, 201, 109)
        elif "north east" in chapter:
            kind, wall, roof, sign = "FARMHOUSE", (207, 174, 113), (130, 79, 48), (223, 194, 125)
        elif "volcano" in chapter:
            kind, wall, roof, sign = "RESEARCH STATION", (153, 171, 161), (67, 80, 83), (88, 205, 213)
        else:
            kind, wall, roof, sign = "CONTROL FACILITY", (132, 148, 148), (49, 61, 69), (83, 218, 199)

        building_index = {
            "HOUSE": 2, "FIELD SHELTER": 17, "CLINIC": 5,
            "HARBOR OFFICE": 20, "FARMHOUSE": 8,
            "RESEARCH STATION": 15, "CONTROL FACILITY": 22,
        }.get(kind, 2)
        establishment = (sprite("locations", "world_engine") if building_index == 22
                          else scaled("buildings", f"building_{building_index:02}", (176, 132)))
        if establishment:
            world_rect = pygame.Rect(232, 48, 176, 132)
            rect = camera.apply(world_rect)
            size = (max(1, round(establishment.get_width() * camera.zoom)),
                    max(1, round(establishment.get_height() * camera.zoom)))
            establishment = pygame.transform.scale(establishment, size)
            surface.blit(establishment, establishment.get_rect(midbottom=(rect.centerx,
                                                                            rect.bottom)))
            return

        # The establishing shot uses the same 2D top-down angle as gameplay.
        # Its larger footprint lets the reduced character sprites read at scale.
        world_rect = pygame.Rect(250, 42, 140, 82)
        rect = camera.apply(world_rect)
        z = camera.zoom
        pygame.draw.ellipse(surface, (35, 54, 49), rect.inflate(round(14 * z), round(5 * z)).move(0, round(3 * z)))
        body = pygame.Rect(rect.x + round(7 * z), rect.y + round(18 * z),
                           rect.w - round(14 * z), rect.h - round(20 * z))
        pygame.draw.rect(surface, wall, body)
        pygame.draw.rect(surface, (61, 54, 47), body, max(1, round(2 * z)))
        roof_points = ((rect.x - round(3 * z), rect.y + round(20 * z)),
                       (rect.centerx, rect.y - round(4 * z)),
                       (rect.right + round(3 * z), rect.y + round(20 * z)))
        pygame.draw.polygon(surface, roof, roof_points)
        pygame.draw.lines(surface, (52, 47, 41), False, roof_points, max(1, round(2 * z)))

        door = pygame.Rect(rect.centerx - round(9 * z), body.bottom - round(23 * z),
                           round(18 * z), round(23 * z))
        pygame.draw.rect(surface, (71, 53, 43), door)
        pygame.draw.rect(surface, (38, 43, 41), door, max(1, round(z)))
        for wx in (body.x + round(13 * z), body.right - round(25 * z)):
            window = pygame.Rect(wx, body.y + round(9 * z), round(13 * z), round(12 * z))
            pygame.draw.rect(surface, (102, 166, 174), window)
            pygame.draw.rect(surface, (242, 224, 183), window, max(1, round(z)))
            pygame.draw.line(surface, (242, 224, 183), window.midtop, window.midbottom, 1)

        badge = pygame.Rect(rect.centerx - round(32 * z), body.y - round(10 * z),
                            round(64 * z), round(10 * z))
        pygame.draw.rect(surface, (15, 31, 37), badge)
        pygame.draw.rect(surface, sign, badge, 1)
        label = theme.get_font("tiny").render(kind, False, (250, 242, 218))
        label = pygame.transform.scale(label, (max(1, round(label.get_width() * z)),
                                                max(1, round(label.get_height() * z))))
        surface.blit(label, label.get_rect(center=badge.center))

    def _build_details_surface(self):
        world = self.details_surface
        for x, y, kind, variant in self.details:
            sx, sy = x, y
            if kind == "grass":
                pygame.draw.line(world, (45, 94, 58), (sx, sy + 3), (sx - 2, sy - 2), 1)
                pygame.draw.line(world, (120, 164, 91), (sx, sy + 3), (sx + 2, sy - 3), 1)
                pygame.draw.line(world, (80, 132, 76), (sx, sy + 3), (sx + 1, sy - 1), 1)
            elif kind == "flower":
                color = ((246, 207, 112), (237, 154, 150), (234, 226, 183))[variant]
                pygame.draw.line(world, (63, 114, 69), (sx, sy + 4), (sx, sy), 1)
                pygame.draw.circle(world, color, (sx, sy), 2)
                pygame.draw.circle(world, (255, 240, 195), (sx, sy), 1)
            elif kind in ("stone", "rock"):
                color = (105, 111, 103) if kind == "stone" else (81, 73, 70)
                pygame.draw.ellipse(world, (42, 68, 50), (sx - 5, sy + 2, 11, 4))
                pygame.draw.polygon(world, color, [(sx - 4, sy + 2), (sx - 2, sy - 3),
                                                    (sx + 2, sy - 4), (sx + 5, sy + 1)])
                pygame.draw.line(world, (157, 151, 130), (sx - 1, sy - 2), (sx + 2, sy - 3), 1)
            elif kind == "shrub":
                pygame.draw.ellipse(world, (43, 87, 57), (sx - 6, sy - 1, 13, 7))
                pygame.draw.circle(world, (80, 135, 76), (sx - 2, sy), 3)
                pygame.draw.circle(world, (105, 153, 82), (sx + 3, sy + 1), 3)
            elif kind == "crack":
                pygame.draw.lines(world, (80, 77, 71), False,
                                  [(sx - 4, sy - 3), (sx, sy), (sx - 1, sy + 2), (sx + 4, sy + 4)], 1)
                pygame.draw.line(world, (80, 77, 71), (sx, sy), (sx + 3, sy - 3), 1)
            elif kind == "ash":
                pygame.draw.circle(world, (116, 105, 96), (sx, sy), 2)
                pygame.draw.circle(world, (157, 144, 124), (sx + 4, sy + 2), 1)
            elif kind == "char":
                pygame.draw.ellipse(world, (75, 70, 56), (sx - 4, sy, 9, 4))
                pygame.draw.line(world, (113, 91, 62), (sx - 2, sy + 1), (sx + 3, sy - 2), 1)
            elif kind == "reed":
                pygame.draw.line(world, (52, 111, 78), (sx, sy + 4), (sx - 1, sy - 4), 1)
                pygame.draw.line(world, (83, 142, 91), (sx + 2, sy + 4), (sx + 4, sy - 2), 1)
    def draw_details(self, surface, camera):
        zoom = camera.zoom
        size = (max(1, round(self.width * zoom)), max(1, round(self.height * zoom)))
        key = ("details", size)
        if key not in self.zoom_tiles:
            self.zoom_tiles[key] = pygame.transform.scale(self.details_surface, size)
        x = round(camera.offset.x * zoom)
        y = round(camera.offset.y * zoom)
        surface.blit(self.zoom_tiles[key], (camera.viewport.x - x, camera.viewport.y - y))
