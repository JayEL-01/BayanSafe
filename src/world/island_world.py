"""Map-aligned coordinates for the shared, walkable Mount Talon island."""

from __future__ import annotations

import pygame


# The source illustration is an M-screen reference at native pixel size. The
# walkable world uses a uniform 2x coordinate transform; it never draws the
# labeled reference image as ground.
MAP_SIZE = (1323, 1189)
MAP_SCALE = 2
WORLD_SIZE = (MAP_SIZE[0] * MAP_SCALE + 322, MAP_SIZE[1] * MAP_SCALE)

# Existing mission scenes remain 640x360 local spaces. Their player start is
# placed at each approved map anchor, so mission data and saves keep their IDs
# and local coordinates while the scenes sit in the new island coordinate map.
CELL_SIZE = (640, 360)  # legacy name; this is a scene footprint, not a grid cell.
SCENE_SIZE = CELL_SIZE
DEFAULT_PLAYER_START = (26, 30)

REGION_ANCHORS = {
    "Home Village": (230, 472),
    "North West Plateau": (300, 330),
    "Central Town": (492, 596),
    "Harbor": (181, 749),
    "North East Plains": (1177, 416),
    "Volcano Valleys": (526, 415),
    "Main Control Room": (785, 226),
}

# Practical placement bounds in source-map pixels. These are editorial guides
# inside the approved map regions; IslandGeometry remains authoritative for
# whether a particular object footprint is actually walkable.
REGION_PLACEMENT_BOUNDS = {
    "Home Village": (76, 382, 324, 544),
    "North West Plateau": (278, 292, 426, 420),
    "Central Town": (356, 508, 650, 680),
    "Harbor": (276, 660, 336, 810),
    "North East Plains": (1018, 326, 1290, 506),
    "Volcano Valleys": (394, 325, 594, 486),
    "Main Control Room": (666, 150, 902, 316),
}

REGION_SCENES = {
    "Home Village": "home_island_tutorial",
    "North West Plateau": "earthquake",
    "Central Town": "flash_fire",
    "Harbor": "harbor_flash_flood",
    "North East Plains": "plains_typhoon",
    "Volcano Valleys": "silence_volcano",
    "Main Control Room": "final_shutdown",
}

STAGE_REGIONS = {
    "home_island_tutorial": "Home Village",
    "earthquake": "North West Plateau",
    "landslide": "North West Plateau",
    "calm_before_wave": "North West Plateau",
    "tsunami": "North West Plateau",
    "flash_fire": "Central Town",
    "central_earthquake": "Central Town",
    "central_typhoon": "Central Town",
    "central_flash_flood": "Central Town",
    "harbor_flash_flood": "Harbor",
    "harbor_typhoon": "Harbor",
    "harbor_severe_flood": "Harbor",
    "harbor_fire_tsunami": "Harbor",
    "plains_typhoon": "North East Plains",
    "plains_severe_flood": "North East Plains",
    "plains_landslide": "North East Plains",
    "plains_quake_volcano": "North East Plains",
    "silence_volcano": "Volcano Valleys",
    "volcano_flash_flood": "Volcano Valleys",
    "final_typhoon_flood": "Volcano Valleys",
    "final_shutdown": "Main Control Room",
}


def map_to_world(point):
    """Convert a native map pixel coordinate to a world pixel coordinate."""
    return tuple(round(value * MAP_SCALE) for value in point)


def world_to_map(point):
    """Convert a world point to native source-map pixel coordinates."""
    return tuple(value / MAP_SCALE for value in point)


def origin_for_region(region, player_start=DEFAULT_PLAYER_START):
    """Return a scene origin that places its normal spawn on the region anchor."""
    anchor = map_to_world(REGION_ANCHORS.get(region, REGION_ANCHORS["Home Village"]))
    return anchor[0] - player_start[0], anchor[1] - player_start[1]


def region_for_stage(stage_id):
    return STAGE_REGIONS.get(stage_id, "Volcano Valleys")


def origin_for_stage(stage_id, player_start=DEFAULT_PLAYER_START):
    """Map a legacy stage ID to its approved geography without changing the ID."""
    region = region_for_stage(stage_id)
    if stage_id == "final_shutdown":
        player_start = player_start or (32, 300)
    return origin_for_region(region, player_start or DEFAULT_PLAYER_START)


def local_to_world_rect(rect, origin):
    return pygame.Rect(rect).move(origin)


class RegionCamera:
    """Camera adapter that draws one local mission scene in world coordinates."""

    def __init__(self, camera, origin):
        self.camera = camera
        self.origin = pygame.Vector2(origin)
        self.offset = camera.offset - self.origin
        self.zoom = camera.zoom
        self.viewport = camera.viewport

    def apply(self, rect):
        return self.camera.apply(pygame.Rect(rect).move(self.origin))
