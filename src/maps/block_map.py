"""Code-rendered Plain-Colored Environment Block Map for BayanSafe.

Zero external image assets are used for the environment. All buildings,
roads, bridges, water, hazards, safe zones, and items are rendered via code
as flat colored rectangles with high readability and crisp labels.
"""

import math
from typing import List, Dict, Any, Optional, Tuple
import pygame

from src.config.palette import (
    COLOR_GROUND_DEFAULT,
    COLOR_BUILDING_HOUSE,
    COLOR_BUILDING_DAMAGED,
    COLOR_BUILDING_SHELTER,
    COLOR_BUILDING_HOSPITAL,
    COLOR_BUILDING_RESEARCH,
    COLOR_BUILDING_COMMERCIAL,
    COLOR_BUILDING_WAREHOUSE,
    COLOR_ROAD,
    COLOR_PATH,
    COLOR_BRIDGE,
    COLOR_WATER,
    COLOR_TREE_FOLIAGE,
    COLOR_TREE_TRUNK,
    COLOR_WALL_COLLISION,
    COLOR_HAZARD_FLOOD,
    COLOR_HAZARD_FIRE,
    COLOR_HAZARD_LANDSLIDE,
    COLOR_HAZARD_ASH,
    COLOR_HAZARD_TSUNAMI,
    COLOR_SAFE_ZONE,
    COLOR_ITEM_GOBAG,
    COLOR_ITEM_WATER,
    COLOR_ITEM_FOOD,
    COLOR_ITEM_FIRSTAID,
    COLOR_ITEM_FLASHLIGHT,
    COLOR_ITEM_RADIO,
    COLOR_ITEM_KEY,
    COLOR_ITEM_LOG,
    COLOR_ITEM_MAP,
    COLOR_UI_TEXT,
    COLOR_UI_ACCENT,
)
from src.ui import theme
from src.entities.world_art import icon_surface, item_art_name


class MapItem:
    def __init__(self, item_id: str, label: str, rect: pygame.Rect, color: Tuple[int, int, int]):
        self.item_id = item_id
        self.label = label
        self.rect = rect
        self.color = color
        self.collected = False


class MapElement:
    def __init__(
        self,
        elem_type: str,
        rect: pygame.Rect,
        color: Tuple[int, int, int],
        label: str = "",
        solid: bool = False,
        hazard_type: Optional[str] = None,
        trigger_id: Optional[str] = None,
    ):
        self.elem_type = elem_type
        self.rect = rect
        self.color = color
        self.label = label
        self.solid = solid
        self.hazard_type = hazard_type
        self.trigger_id = trigger_id


class BlockMap:
    def __init__(
        self,
        location_name: str,
        width: int = 640,
        height: int = 360,
        ground_color: Tuple[int, int, int] = COLOR_GROUND_DEFAULT,
    ):
        self.location_name = location_name
        self.width = width
        self.height = height
        self.ground_color = ground_color

        self.elements: List[MapElement] = []
        self.collision_rects: List[pygame.Rect] = []
        self._water_collision: List[pygame.Rect] = []  # water pieces currently blocking movement
        self.hazard_zones: List[MapElement] = []
        self.safe_zones: List[MapElement] = []
        self.triggers: List[MapElement] = []
        self.items: List[MapItem] = []
        self.spawn_point = (80, 80)
        self.npc_spawns: List[Dict[str, Any]] = []

        self.anim_timer: float = 0.0

        # Boundary collision borders
        self._add_boundary_walls()

    def _add_boundary_walls(self, thickness: int = 16):
        top = MapElement("wall", pygame.Rect(0, 0, self.width, thickness), COLOR_WALL_COLLISION, solid=True)
        bottom = MapElement("wall", pygame.Rect(0, self.height - thickness, self.width, thickness), COLOR_WALL_COLLISION, solid=True)
        left = MapElement("wall", pygame.Rect(0, 0, thickness, self.height), COLOR_WALL_COLLISION, solid=True)
        right = MapElement("wall", pygame.Rect(self.width - thickness, 0, thickness, self.height), COLOR_WALL_COLLISION, solid=True)
        for w in (top, bottom, left, right):
            self.elements.append(w)
            self.collision_rects.append(w.rect)

    def add_road(self, x: int, y: int, w: int, h: int, color: Tuple[int, int, int] = COLOR_ROAD):
        elem = MapElement("road", pygame.Rect(x, y, w, h), color, solid=False)
        self.elements.append(elem)
        return elem

    def add_path(self, x: int, y: int, w: int, h: int):
        elem = MapElement("path", pygame.Rect(x, y, w, h), COLOR_PATH, solid=False)
        self.elements.append(elem)
        return elem

    def add_water(self, x: int, y: int, w: int, h: int):
        elem = MapElement("water", pygame.Rect(x, y, w, h), COLOR_WATER, label="WATER", solid=True)
        self.elements.append(elem)
        self._sync_water_collision()
        return elem

    def add_bridge(self, x: int, y: int, w: int, h: int):
        elem = MapElement("bridge", pygame.Rect(x, y, w, h), COLOR_BRIDGE, label="BRIDGE", solid=False)
        self.elements.append(elem)
        # A bridge is a walkable crossing over water: its footprint is carved
        # out of the water collision (see _sync_water_collision).
        self._sync_water_collision()
        return elem

    def _sync_water_collision(self):
        """Rebuild the water collision pieces.

        Water blocks movement, but bridge footprints carved through it stay
        walkable, and safe zones must remain clear. Rebuilding from the element
        list keeps this true regardless of the order elements are added in.
        """
        for piece in self._water_collision:
            if piece in self.collision_rects:
                self.collision_rects.remove(piece)
        self._water_collision = []

        gaps = [e.rect for e in self.elements if e.elem_type in ("bridge", "safe_zone")]
        for water in (e for e in self.elements if e.elem_type == "water"):
            pieces = [water.rect]
            for gap in gaps:
                pieces = [part for piece in pieces for part in self._split_rect_around(piece, gap)]
            for piece in pieces:
                if piece.w > 0 and piece.h > 0:
                    self.collision_rects.append(piece)
                    self._water_collision.append(piece)

    @staticmethod
    def _split_rect_around(rect: pygame.Rect, gap: pygame.Rect) -> List[pygame.Rect]:
        """Split `rect` into up to four sub-rects that exclude the overlap with `gap`."""
        carve = gap.clip(rect)
        if carve.w <= 0 or carve.h <= 0:
            return [rect]
        pieces: List[pygame.Rect] = []
        if carve.top > rect.top:
            pieces.append(pygame.Rect(rect.x, rect.y, rect.w, carve.top - rect.top))
        if rect.bottom > carve.bottom:
            pieces.append(pygame.Rect(rect.x, carve.bottom, rect.w, rect.bottom - carve.bottom))
        if carve.left > rect.x:
            pieces.append(pygame.Rect(rect.x, carve.top, carve.left - rect.x, carve.h))
        if rect.right > carve.right:
            pieces.append(pygame.Rect(carve.right, carve.top, rect.right - carve.right, carve.h))
        return pieces


    def add_building(
        self,
        btype: str,
        label: str,
        x: int,
        y: int,
        w: int,
        h: int,
        solid: Optional[bool] = None,
        trigger_id: Optional[str] = None,
    ):
        if solid is None:
            solid = (btype != "shelter")

        color_map = {
            "house": COLOR_BUILDING_HOUSE,
            "damaged_house": COLOR_BUILDING_DAMAGED,
            "shelter": COLOR_BUILDING_SHELTER,
            "clinic": COLOR_BUILDING_HOSPITAL,
            "research": COLOR_BUILDING_RESEARCH,
            "commercial": COLOR_BUILDING_COMMERCIAL,
            "warehouse": COLOR_BUILDING_WAREHOUSE,
        }
        color = color_map.get(btype, COLOR_BUILDING_HOUSE)
        elem = MapElement(btype, pygame.Rect(x, y, w, h), color, label=label, solid=solid, trigger_id=trigger_id)
        self.elements.append(elem)
        if solid:
            self.collision_rects.append(elem.rect)
        if trigger_id:
            self.triggers.append(elem)
        return elem

    def add_tree(self, x: int, y: int):
        trunk = MapElement("tree_trunk", pygame.Rect(x + 4, y + 10, 4, 6), COLOR_TREE_TRUNK, solid=True)
        foliage = MapElement("tree", pygame.Rect(x, y, 12, 12), COLOR_TREE_FOLIAGE, solid=True)
        self.elements.append(trunk)
        self.elements.append(foliage)
        self.collision_rects.append(foliage.rect)

    def add_hazard_zone(self, hazard_type: str, x: int, y: int, w: int, h: int, label: str = ""):
        color_map = {
            "flood": COLOR_HAZARD_FLOOD,
            "fire": COLOR_HAZARD_FIRE,
            "landslide": COLOR_HAZARD_LANDSLIDE,
            "ash": COLOR_HAZARD_ASH,
            "tsunami": COLOR_HAZARD_TSUNAMI,
        }
        color = color_map.get(hazard_type, COLOR_HAZARD_FLOOD)
        lbl = label if label else f"{hazard_type.upper()} ZONE"
        solid = (hazard_type == "landslide")
        elem = MapElement(
            f"hazard_{hazard_type}",
            pygame.Rect(x, y, w, h),
            color,
            label=lbl,
            solid=solid,
            hazard_type=hazard_type,
        )
        self.elements.append(elem)
        self.hazard_zones.append(elem)
        if solid:
            self.collision_rects.append(elem.rect)
        return elem

    def add_safe_zone(self, x: int, y: int, w: int, h: int, label: str = "HIGH GROUND", trigger_id: str = "evac_safe"):
        sz_rect = pygame.Rect(x, y, w, h)
        # Ensure the safe high ground zone is 100% walkable by clearing any collision obstacles inside it
        self.collision_rects = [r for r in self.collision_rects if not r.colliderect(sz_rect)]
        elem = MapElement(
            "safe_zone",
            sz_rect,
            COLOR_SAFE_ZONE,
            label=label,
            solid=False,
            trigger_id=trigger_id,
        )
        self.elements.append(elem)
        self.safe_zones.append(elem)
        self.triggers.append(elem)
        return elem

    def add_item(self, item_id: str, label: str, x: int, y: int):
        color_map = {
            "gobag": COLOR_ITEM_GOBAG,
            "water": COLOR_ITEM_WATER,
            "food": COLOR_ITEM_FOOD,
            "firstaid": COLOR_ITEM_FIRSTAID,
            "flashlight": COLOR_ITEM_FLASHLIGHT,
            "radio": COLOR_ITEM_RADIO,
            "keycard": COLOR_ITEM_KEY,
            "log": COLOR_ITEM_LOG,
            "map": COLOR_ITEM_MAP,
        }
        color = color_map.get(item_id, COLOR_ITEM_GOBAG)
        item = MapItem(item_id, label, pygame.Rect(x, y, 10, 10), color)
        self.items.append(item)
        return item

    def check_collision(self, rect: pygame.Rect) -> bool:
        return any(rect.colliderect(coll) for coll in self.collision_rects)

    def get_active_hazard_at(self, rect: pygame.Rect) -> Optional[str]:
        for hz in self.hazard_zones:
            if hz.rect.colliderect(rect):
                return hz.hazard_type
        return None

    def check_triggers(self, rect: pygame.Rect) -> List[str]:
        triggered = []
        for tr in self.triggers:
            if tr.trigger_id and tr.rect.colliderect(rect):
                triggered.append(tr.trigger_id)
        return triggered

    def check_item_pickup(self, rect: pygame.Rect) -> Optional[MapItem]:
        for it in self.items:
            if not it.collected and it.rect.colliderect(rect):
                it.collected = True
                return it
        return None

    def update(self, dt: float):
        self.anim_timer += dt

    def draw(self, surface: pygame.Surface, camera=None):
        surface.fill(self.ground_color)

        def to_screen(r: pygame.Rect) -> pygame.Rect:
            return camera.apply(r) if camera else r

        # Roads, paths, water, bridges
        for elem in self.elements:
            if elem.elem_type in ("road", "path", "water", "bridge"):
                s_rect = to_screen(elem.rect)
                pygame.draw.rect(surface, elem.color, s_rect)
                if elem.elem_type == "bridge":
                    pygame.draw.rect(surface, (80, 55, 35), s_rect, 1)

        # Hazard danger zones
        pulse = 0.5 + 0.5 * math.sin(self.anim_timer * 4.0)
        for hz in self.hazard_zones:
            s_rect = to_screen(hz.rect)
            hazard_surf = pygame.Surface((s_rect.w, s_rect.h), pygame.SRCALPHA)
            base_color = hz.color
            alpha = int(140 + 60 * pulse)
            hazard_surf.fill((*base_color, alpha))
            surface.blit(hazard_surf, (s_rect.x, s_rect.y))
            pygame.draw.rect(surface, (255, 255, 255), s_rect, 1)
            if hz.label and 24 <= s_rect.centerx <= 296 and 14 <= s_rect.centery <= 166:
                theme.draw_text(
                    surface,
                    hz.label,
                    (s_rect.centerx, s_rect.centery - 3),
                    size="tiny",
                    color=COLOR_UI_TEXT,
                    anchor="center",
                )

        # Safe zones
        for sz in self.safe_zones:
            s_rect = to_screen(sz.rect)
            safe_surf = pygame.Surface((s_rect.w, s_rect.h), pygame.SRCALPHA)
            safe_surf.fill((*COLOR_SAFE_ZONE, 160))
            surface.blit(safe_surf, (s_rect.x, s_rect.y))
            pygame.draw.rect(surface, (180, 255, 180), s_rect, 2)
            if sz.label and 24 <= s_rect.centerx <= 296 and 14 <= s_rect.centery <= 166:
                theme.draw_text(
                    surface,
                    sz.label,
                    (s_rect.centerx, s_rect.centery - 3),
                    size="tiny",
                    color=(255, 255, 255),
                    anchor="center",
                )

        # Buildings, structures, walls, trees
        for elem in self.elements:
            if elem.elem_type in ("road", "path", "water", "bridge", "hazard_flood", "hazard_fire", "hazard_landslide", "hazard_ash", "hazard_tsunami", "safe_zone"):
                continue

            s_rect = to_screen(elem.rect)
            pygame.draw.rect(surface, elem.color, s_rect)

            if elem.solid and elem.elem_type not in ("tree_trunk", "tree", "wall"):
                darker = (max(0, elem.color[0] - 30), max(0, elem.color[1] - 30), max(0, elem.color[2] - 30))
                pygame.draw.rect(surface, darker, s_rect, 2)
                if elem.label and 24 <= s_rect.centerx <= 296 and 14 <= s_rect.centery <= 166:
                    theme.draw_text(
                        surface,
                        elem.label,
                        (s_rect.centerx, s_rect.centery - 3),
                        size="tiny",
                        color=COLOR_UI_TEXT,
                        anchor="center",
                        shadow=True,
                    )
            elif elem.elem_type == "wall":
                pygame.draw.rect(surface, (15, 15, 20), s_rect, 1)

        # Items (hard-coded pixel sprites, shared with the pickup system)
        for item in self.items:
            if item.collected:
                continue
            s_rect = to_screen(item.rect)
            bob = int(math.sin(self.anim_timer * 6.0) * 2)
            cx = s_rect.centerx
            cy = s_rect.centery + bob
            pygame.draw.ellipse(surface, (10, 14, 12), (cx - 5, cy + 5, 10, 4))
            icon = icon_surface(item_art_name(item.item_id, item.label), 1)
            surface.blit(icon, icon.get_rect(center=(cx, cy)))
            if 20 <= cx <= 300 and 14 <= s_rect.top <= 166:
                theme.draw_text(
                    surface,
                    item.label,
                    (cx, s_rect.top - 6 + bob),
                    size="tiny",
                    color=COLOR_UI_ACCENT,
                    anchor="center",
                    shadow=True,
                )
