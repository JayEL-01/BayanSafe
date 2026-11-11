"""Centralized Asset Manager and Pixel-Block Placeholder Generator for BayanSafe.

Handles loading, caching, and fallback generation of all pixel-art game assets.
Separates assets into:
  - assets/shared/ (characters, npcs, buildings, environment, objects, ui)
  - assets/chapters/<chapter_id>/ (backgrounds, characters, npcs, buildings, objects, environment)

Provides documented specifications for replacing placeholders with custom graphics.
"""
import os
from pathlib import Path
from typing import Dict, Optional, Tuple, Union
import pygame

# Root paths
PROJECT_ROOT = Path(__file__).resolve().parents[2]
ASSETS_DIR = PROJECT_ROOT / "assets"
SHARED_DIR = ASSETS_DIR / "shared"
CHAPTERS_ASSETS_DIR = ASSETS_DIR / "chapters"

# Ensure directories exist
for cat in ("characters", "npcs", "buildings", "environment", "objects", "ui"):
    (SHARED_DIR / cat).mkdir(parents=True, exist_ok=True)


# -----------------------------------------------------------------------------
# PALETTE DEFINITIONS FOR PIXEL-BLOCK AESTHETIC
# -----------------------------------------------------------------------------
COLOR_OUTLINE = (38, 28, 36)
COLOR_SKIN = (235, 182, 142)
COLOR_SKIN_SHADOW = (196, 142, 105)
COLOR_HAIR_DARK = (45, 32, 28)
COLOR_HAIR_BROWN = (88, 55, 38)
COLOR_WHITE = (248, 248, 244)
COLOR_GLASS = (120, 185, 205)
COLOR_WOOD = (138, 92, 58)
COLOR_WOOD_DARK = (88, 56, 34)
COLOR_WOOD_LIGHT = (182, 132, 88)
COLOR_STONE = (128, 132, 136)
COLOR_STONE_DARK = (82, 86, 92)
COLOR_STONE_LIGHT = (175, 178, 180)
COLOR_ROOF_RED = (176, 74, 58)
COLOR_ROOF_BLUE = (64, 108, 148)
COLOR_ROOF_GREEN = (68, 130, 88)
COLOR_GRASS = (92, 154, 76)
COLOR_GRASS_DARK = (62, 114, 52)
COLOR_TRUNK = (108, 72, 44)
COLOR_WATER = (64, 138, 172)
COLOR_SAND = (224, 198, 138)


class AssetManager:
    """Centralized manager for loading and retrieving game assets with fallback placeholders."""

    _cache: Dict[Tuple[str, str, Optional[Tuple[int, int]]], pygame.Surface] = {}

    @classmethod
    def get_shared_path(cls, category: str, filename: str) -> Path:
        """Return path in assets/shared/."""
        if not filename.endswith(".png"):
            filename = f"{filename}.png"
        return SHARED_DIR / category / filename

    @classmethod
    def get_chapter_path(cls, chapter_id: str, category: str, filename: str) -> Path:
        """Return path in assets/chapters/<chapter_id>/."""
        if not filename.endswith(".png"):
            filename = f"{filename}.png"
        return CHAPTERS_ASSETS_DIR / chapter_id / category / filename

    @classmethod
    def load(
        cls,
        category: str,
        name: str,
        chapter_id: Optional[str] = None,
        size: Optional[Tuple[int, int]] = None,
    ) -> pygame.Surface:
        """Load an asset by category and name.

        Search order:
          1. assets/chapters/<chapter_id>/<category>/<name>.png
          2. chapters/<chapter_id>/assets/<category>/<name>.png
          3. assets/shared/<category>/<name>.png
          4. assets/images/<category>/<name>.png (legacy fallback)
          5. Procedural pixel-block generator
        """
        filename = name if name.endswith(".png") else f"{name}.png"
        cache_key = (category, f"{chapter_id or 'shared'}:{filename}", size)
        if cache_key in cls._cache:
            return cls._cache[cache_key]

        candidates = []
        if chapter_id:
            candidates.append(CHAPTERS_ASSETS_DIR / chapter_id / category / filename)
            candidates.append(PROJECT_ROOT / "chapters" / chapter_id / "assets" / category / filename)
        candidates.append(SHARED_DIR / category / filename)
        candidates.append(ASSETS_DIR / "images" / category / filename)
        candidates.append(ASSETS_DIR / "images" / "characters" / filename)
        candidates.append(ASSETS_DIR / "images" / "game_art" / category / filename)
        candidates.append(ASSETS_DIR / "images" / "game_art" / "characters" / filename)
        candidates.append(ASSETS_DIR / "images" / "game_art" / "buildings" / filename)
        candidates.append(ASSETS_DIR / "images" / "game_art" / "items" / filename)
        candidates.append(ASSETS_DIR / "images" / "game_art" / "effects" / filename)
        candidates.append(ASSETS_DIR / "images" / "world" / filename)
        candidates.append(ASSETS_DIR / "images" / "ui" / filename)

        surface = None
        for path in candidates:
            if path.exists() and path.is_file():
                try:
                    surface = pygame.image.load(str(path)).convert_alpha()
                    break
                except Exception:
                    continue

        if surface is None:
            surface = cls.create_placeholder(category, name, size)

        if size and surface.get_size() != size:
            surface = pygame.transform.scale(surface, size)

        cls._cache[cache_key] = surface
        return surface

    @classmethod
    def create_placeholder(
        cls, category: str, name: str, size: Optional[Tuple[int, int]] = None
    ) -> pygame.Surface:
        """Generate a clean, styled pixel-block placeholder surface."""
        name_clean = name.replace(".png", "").lower()

        if category in ("characters", "npcs"):
            target_size = size or (16, 20)
            return cls._generate_character_sprite(name_clean, target_size)
        elif category == "buildings":
            target_size = size or (48, 40)
            return cls._generate_building_sprite(name_clean, target_size)
        elif category == "objects":
            target_size = size or (16, 16)
            return cls._generate_object_sprite(name_clean, target_size)
        elif category == "environment":
            target_size = size or (24, 24)
            return cls._generate_environment_sprite(name_clean, target_size)
        elif category == "ui":
            target_size = size or (32, 32)
            return cls._generate_ui_sprite(name_clean, target_size)
        else:
            target_size = size or (24, 24)
            return cls._generate_generic_block(name_clean, target_size)

    # -------------------------------------------------------------------------
    # PIXEL-BLOCK GENERATORS
    # -------------------------------------------------------------------------
    @classmethod
    def _generate_character_sprite(cls, name: str, size: Tuple[int, int]) -> pygame.Surface:
        """Create a clean pixel character sprite with distinct shirt and pants colors."""
        w, h = size
        surf = pygame.Surface((w, h), pygame.SRCALPHA)

        # Distinguishable colors per character/role
        shirt_colors = {
            "juan": (230, 160, 40),       # Amber orange
            "maria": (45, 160, 175),      # Cyan teal
            "engr_rica": (220, 100, 35),  # Engineer Safety Orange
            "rica": (220, 100, 35),
            "mang_kiko": (65, 125, 185),  # Fisherman Blue
            "mang_pido": (75, 140, 70),   # Farm Green
            "nanay_cora": (175, 90, 145), # Magenta/Violet
            "tanod_tomas": (45, 80, 140), # Tanod Navy Blue
            "kap_ben": (185, 60, 55),     # Barangay Red
            "lola_nena": (145, 115, 160), # Elder Lilac
            "lola_teresa": (145, 115, 160),
            "dr_elena_reyes": (235, 235, 240), # Doctor Labcoat White
            "mayor_cruz": (120, 80, 140), # Formal Purple
            "nurse_joy": (240, 180, 195), # Nurse Pastel Pink
            "berto": (190, 140, 60),      # Tan Ochre
            "dock_worker": (160, 110, 60),# Harbor Khaki
            "trapped_resident": (180, 70, 70), # Distressed Red
        }
        shirt = shirt_colors.get(name, (140, 120, 100))
        hair = (220, 120, 30) if "rica" in name else (190, 180, 175) if ("lola" in name or "pido" in name) else COLOR_HAIR_DARK
        pants = (45, 55, 75) if "tanod" in name else (60, 65, 85)

        # Proportions: head (top 40%), torso (middle 35%), legs (bottom 25%)
        head_h = max(4, int(h * 0.40))
        torso_h = max(4, int(h * 0.35))
        legs_h = h - head_h - torso_h

        cx = w // 2
        hw = max(3, int(w * 0.35))

        # Shadow
        pygame.draw.ellipse(surf, (20, 20, 25, 140), (cx - hw, h - 3, hw * 2, 3))

        # Legs
        leg_w = max(1, hw - 1)
        pygame.draw.rect(surf, pants, (cx - hw, head_h + torso_h, leg_w, legs_h))
        pygame.draw.rect(surf, pants, (cx + 1, head_h + torso_h, leg_w, legs_h))

        # Torso
        torso_rect = pygame.Rect(cx - hw - 1, head_h, hw * 2 + 2, torso_h)
        pygame.draw.rect(surf, shirt, torso_rect)
        pygame.draw.rect(surf, COLOR_OUTLINE, torso_rect, 1)

        # Head / Hair
        head_rect = pygame.Rect(cx - hw, 1, hw * 2, head_h)
        pygame.draw.rect(surf, COLOR_SKIN, head_rect)
        # Hair top
        hair_h = max(2, head_h // 2)
        pygame.draw.rect(surf, hair, (cx - hw, 1, hw * 2, hair_h))
        # Eyes (2 pixels)
        eye_y = 1 + hair_h
        surf.set_at((cx - hw + 1, eye_y), (30, 25, 30))
        surf.set_at((cx + hw - 2, eye_y), (30, 25, 30))
        pygame.draw.rect(surf, COLOR_OUTLINE, head_rect, 1)

        return surf

    @classmethod
    def _generate_building_sprite(cls, name: str, size: Tuple[int, int]) -> pygame.Surface:
        """Create a pixel-block building with distinct roof, door, windows, and signage."""
        w, h = size
        surf = pygame.Surface((w, h), pygame.SRCALPHA)

        # Pick palette based on building type
        if "shelter" in name or "evacuation" in name:
            roof_color = COLOR_ROOF_GREEN
            wall_color = (235, 230, 205)
            sign_color = (60, 150, 80)
            sign_text = "S"
        elif "hospital" in name or "clinic" in name:
            roof_color = COLOR_ROOF_RED
            wall_color = (245, 245, 248)
            sign_color = (210, 50, 50)
            sign_text = "+"
        elif "school" in name:
            roof_color = COLOR_ROOF_BLUE
            wall_color = (235, 225, 195)
            sign_color = (40, 100, 180)
            sign_text = "SCH"
        elif "shop" in name:
            roof_color = (215, 140, 55)
            wall_color = (230, 215, 180)
            sign_color = (200, 80, 40)
            sign_text = "$"
        elif "fire" in name:
            roof_color = (195, 55, 45)
            wall_color = (220, 210, 200)
            sign_color = (200, 40, 30)
            sign_text = "F"
        elif "police" in name:
            roof_color = (45, 75, 130)
            wall_color = (210, 215, 225)
            sign_color = (40, 70, 140)
            sign_text = "P"
        elif "dock" in name or "fishing" in name:
            roof_color = COLOR_WOOD_DARK
            wall_color = COLOR_WOOD
            sign_color = COLOR_WOOD_LIGHT
            sign_text = ""
        else:
            # Residential house
            roof_color = COLOR_ROOF_RED if "large" in name else (185, 105, 65)
            wall_color = (235, 220, 185)
            sign_color = wall_color
            sign_text = ""

        is_damaged = "damaged" in name

        # Proportions
        roof_h = max(8, int(h * 0.40))
        body_h = h - roof_h - 2
        body_rect = pygame.Rect(4, roof_h, w - 8, body_h)

        # Drop shadow
        pygame.draw.ellipse(surf, (25, 30, 30, 120), (2, h - 5, w - 4, 5))

        # Main wall body
        pygame.draw.rect(surf, wall_color, body_rect)
        pygame.draw.rect(surf, COLOR_OUTLINE, body_rect, 1)

        # Slanted / gabled roof
        roof_pts = [(1, roof_h + 2), (w // 2, 2), (w - 2, roof_h + 2)]
        pygame.draw.polygon(surf, roof_color, roof_pts)
        pygame.draw.polygon(surf, COLOR_OUTLINE, roof_pts, 1)
        # Roof ridge line
        pygame.draw.line(surf, (min(255, roof_color[0] + 35), min(255, roof_color[1] + 35), min(255, roof_color[2] + 35)),
                         (w // 2, 3), (w - 3, roof_h + 1), 1)

        # Door
        door_w = max(8, w // 5)
        door_h = max(10, body_h // 2)
        door_x = (w - door_w) // 2
        door_y = body_rect.bottom - door_h
        door_rect = pygame.Rect(door_x, door_y, door_w, door_h)
        pygame.draw.rect(surf, COLOR_WOOD_DARK, door_rect)
        pygame.draw.rect(surf, COLOR_OUTLINE, door_rect, 1)
        # Door handle
        surf.set_at((door_rect.right - 2, door_rect.centery), (245, 210, 110))

        # Windows
        win_w = max(5, w // 8)
        win_h = max(5, body_h // 3)
        win_y = body_rect.top + 3
        # Left window
        if door_x > win_w + 6:
            lwin = pygame.Rect(body_rect.left + 3, win_y, win_w, win_h)
            pygame.draw.rect(surf, COLOR_GLASS, lwin)
            pygame.draw.rect(surf, COLOR_OUTLINE, lwin, 1)
            pygame.draw.line(surf, COLOR_WHITE, lwin.midtop, lwin.midbottom, 1)
        # Right window
        if body_rect.right - (door_x + door_w) > win_w + 6:
            rwin = pygame.Rect(body_rect.right - win_w - 3, win_y, win_w, win_h)
            pygame.draw.rect(surf, COLOR_GLASS, rwin)
            pygame.draw.rect(surf, COLOR_OUTLINE, rwin, 1)
            pygame.draw.line(surf, COLOR_WHITE, rwin.midtop, rwin.midbottom, 1)

        # Signage badge if applicable
        if sign_text:
            sign_rect = pygame.Rect(w // 2 - 5, body_rect.top - 4, 10, 7)
            pygame.draw.rect(surf, sign_color, sign_rect)
            pygame.draw.rect(surf, COLOR_OUTLINE, sign_rect, 1)

        # If damaged, add cracked/rubble overlay
        if is_damaged:
            pygame.draw.line(surf, COLOR_OUTLINE, (body_rect.left + 2, body_rect.top + 3),
                             (body_rect.left + 8, body_rect.bottom - 4), 1)
            pygame.draw.line(surf, COLOR_OUTLINE, (body_rect.right - 4, body_rect.top + 2),
                             (body_rect.right - 10, body_rect.bottom - 2), 1)
            # Rubble at base
            pygame.draw.rect(surf, COLOR_STONE, (body_rect.left - 2, body_rect.bottom - 3, 5, 3))
            pygame.draw.rect(surf, COLOR_STONE_DARK, (body_rect.right - 3, body_rect.bottom - 4, 4, 4))

        return surf

    @classmethod
    def _generate_object_sprite(cls, name: str, size: Tuple[int, int]) -> pygame.Surface:
        """Create a clean pixel object sprite (first aid, radio, seismometer, etc.)."""
        w, h = size
        surf = pygame.Surface((w, h), pygame.SRCALPHA)

        if "seismo" in name:
            # Seismometer console
            pygame.draw.rect(surf, (85, 95, 105), (1, 3, w - 2, h - 5))
            pygame.draw.rect(surf, (40, 45, 50), (1, 3, w - 2, h - 5), 1)
            # Needle / drum
            pygame.draw.rect(surf, (240, 240, 240), (3, 5, w - 6, h // 2))
            pygame.draw.line(surf, (210, 45, 45), (4, 5 + h // 4), (w - 4, 5 + h // 4), 1)
            # Antenna
            pygame.draw.line(surf, (180, 185, 190), (w // 2, 3), (w // 2, 0), 1)
            surf.set_at((w // 2, 0), (240, 60, 60))
        elif "notice" in name or "board" in name or "monument" in name:
            # Wooden notice board
            pygame.draw.rect(surf, COLOR_WOOD_DARK, (3, h - 6, 2, 6))
            pygame.draw.rect(surf, COLOR_WOOD_DARK, (w - 5, h - 6, 2, 6))
            board_rect = pygame.Rect(1, 1, w - 2, h - 6)
            pygame.draw.rect(surf, COLOR_WOOD, board_rect)
            pygame.draw.rect(surf, COLOR_OUTLINE, board_rect, 1)
            # Paper notice
            paper = pygame.Rect(3, 3, w - 6, h - 10)
            pygame.draw.rect(surf, COLOR_WHITE, paper)
            # Text lines
            pygame.draw.line(surf, (80, 80, 80), (5, 5), (w - 6, 5), 1)
            pygame.draw.line(surf, (80, 80, 80), (5, 7), (w - 8, 7), 1)
        elif "cabinet" in name or "terminal" in name:
            # Metal research terminal / locker
            pygame.draw.rect(surf, (110, 120, 130), (1, 1, w - 2, h - 2))
            pygame.draw.rect(surf, COLOR_OUTLINE, (1, 1, w - 2, h - 2), 1)
            # Glass screen
            pygame.draw.rect(surf, (45, 150, 130), (3, 3, w - 6, h // 2))
            # Blinking LED
            surf.set_at((w - 4, h - 4), (80, 240, 120))
        elif "medkit" in name or "first_aid" in name:
            # First aid box
            box = pygame.Rect(1, 2, w - 2, h - 4)
            pygame.draw.rect(surf, COLOR_WHITE, box)
            pygame.draw.rect(surf, (190, 40, 40), box, 1)
            # Red cross
            cx, cy = w // 2, h // 2
            pygame.draw.line(surf, (220, 40, 40), (cx, cy - 3), (cx, cy + 3), 1)
            pygame.draw.line(surf, (220, 40, 40), (cx - 3, cy), (cx + 3, cy), 1)
        elif "radio" in name:
            # Walkie talkie / radio
            pygame.draw.rect(surf, (55, 65, 65), (2, 3, w - 4, h - 4))
            pygame.draw.rect(surf, COLOR_OUTLINE, (2, 3, w - 4, h - 4), 1)
            # Antenna
            pygame.draw.line(surf, (30, 30, 30), (4, 3), (4, 0), 1)
            # Dial / speaker grill
            pygame.draw.rect(surf, (170, 160, 140), (4, 5, w - 8, 3))
            pygame.draw.line(surf, (30, 30, 30), (5, 10), (w - 6, 10), 1)
            pygame.draw.line(surf, (30, 30, 30), (5, 12), (w - 6, 12), 1)
        elif "water" in name:
            # Water flask / bottle
            bottle = pygame.Rect(w // 2 - 3, 3, 6, h - 4)
            pygame.draw.rect(surf, COLOR_WATER, bottle)
            pygame.draw.rect(surf, COLOR_OUTLINE, bottle, 1)
            # Cap
            pygame.draw.rect(surf, COLOR_WHITE, (w // 2 - 2, 1, 4, 2))
        elif "bag" in name or "backpack" in name:
            # Go-bag backpack
            bag = pygame.Rect(2, 2, w - 4, h - 3)
            pygame.draw.rect(surf, (195, 95, 45), bag)
            pygame.draw.rect(surf, COLOR_OUTLINE, bag, 1)
            # Pocket & buckle
            pygame.draw.rect(surf, (155, 75, 35), (4, h // 2, w - 8, h // 2 - 2))
            surf.set_at((w // 2, h // 2 + 1), (240, 210, 90))
        elif "fissure" in name or "cracks" in name:
            # Earthquake ground fissure
            surf = pygame.Surface((w, h), pygame.SRCALPHA)
            pygame.draw.line(surf, (40, 35, 30), (1, h // 2), (w // 3, h // 3), 2)
            pygame.draw.line(surf, (30, 25, 20), (w // 3, h // 3), (w * 2 // 3, h * 2 // 3), 2)
            pygame.draw.line(surf, (40, 35, 30), (w * 2 // 3, h * 2 // 3), (w - 1, h // 2), 2)
        else:
            # Generic collectible / interactive icon
            cx, cy = w // 2, h // 2
            pygame.draw.circle(surf, (245, 200, 60), (cx, cy), min(w, h) // 2 - 2)
            pygame.draw.circle(surf, COLOR_OUTLINE, (cx, cy), min(w, h) // 2 - 2, 1)
            # Star / exclamation
            surf.set_at((cx, cy - 2), COLOR_WHITE)
            surf.set_at((cx, cy), COLOR_WHITE)
            surf.set_at((cx, cy + 2), COLOR_WHITE)

        return surf

    @classmethod
    def _generate_environment_sprite(cls, name: str, size: Tuple[int, int]) -> pygame.Surface:
        """Create a pixel environment asset (tree, rock, plant, fence, terrain)."""
        w, h = size
        surf = pygame.Surface((w, h), pygame.SRCALPHA)

        if "tree" in name or "palm" in name:
            # Tree with trunk and leafy pixel canopy
            cx = w // 2
            trunk_w = max(2, w // 6)
            trunk_h = max(4, h // 2)
            pygame.draw.rect(surf, COLOR_TRUNK, (cx - trunk_w // 2, h - trunk_h, trunk_w, trunk_h))
            pygame.draw.rect(surf, COLOR_OUTLINE, (cx - trunk_w // 2, h - trunk_h, trunk_w, trunk_h), 1)

            # Leaves / foliage canopy
            leaves_r = max(4, w // 2 - 2)
            leaves_cy = h - trunk_h - 1
            pygame.draw.circle(surf, COLOR_GRASS, (cx, leaves_cy), leaves_r)
            pygame.draw.circle(surf, COLOR_GRASS_DARK, (cx, leaves_cy), leaves_r, 1)
            # Foliage highlight
            pygame.draw.circle(surf, (140, 195, 100), (cx - 2, leaves_cy - 2), leaves_r // 2)
        elif "rock" in name or "stone" in name:
            # Shaded boulder
            cx, cy = w // 2, h // 2
            pts = [(2, h - 3), (w // 4, 3), (w * 3 // 4, 2), (w - 2, h - 4), (w // 2, h - 2)]
            pygame.draw.polygon(surf, COLOR_STONE, pts)
            pygame.draw.polygon(surf, COLOR_OUTLINE, pts, 1)
            # Highlight on top-left
            pygame.draw.line(surf, COLOR_STONE_LIGHT, (w // 4, 4), (w * 3 // 4, 3), 1)
        elif "fence" in name:
            # Wooden fence post & rails
            pygame.draw.rect(surf, COLOR_WOOD, (2, 2, 3, h - 3))
            pygame.draw.rect(surf, COLOR_WOOD, (w - 5, 2, 3, h - 3))
            pygame.draw.rect(surf, COLOR_WOOD_LIGHT, (1, h // 3, w - 2, 2))
            pygame.draw.rect(surf, COLOR_WOOD_LIGHT, (1, h * 2 // 3, w - 2, 2))
        else:
            # Grass / vegetation cluster
            cx, cy = w // 2, h // 2
            pygame.draw.circle(surf, COLOR_GRASS, (cx - 3, cy), 4)
            pygame.draw.circle(surf, (120, 185, 90), (cx + 3, cy - 1), 4)
            pygame.draw.circle(surf, COLOR_OUTLINE, (cx - 3, cy), 4, 1)
            pygame.draw.circle(surf, COLOR_OUTLINE, (cx + 3, cy - 1), 4, 1)

        return surf

    @classmethod
    def _generate_ui_sprite(cls, name: str, size: Tuple[int, int]) -> pygame.Surface:
        """Create clean pixel-art UI icons and lamps."""
        w, h = size
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        cx, cy = w // 2, h // 2

        if "lamp" in name:
            colors = {
                "green": (60, 220, 100),
                "yellow": (245, 220, 60),
                "orange": (245, 140, 40),
                "red": (235, 60, 50),
                "off": (75, 75, 80),
            }
            c = next((v for k, v in colors.items() if k in name), (100, 100, 100))
            pygame.draw.circle(surf, (30, 30, 35), (cx, cy), min(w, h) // 2 - 1)
            pygame.draw.circle(surf, c, (cx, cy), min(w, h) // 2 - 3)
            # Specular dot
            surf.set_at((cx - 1, cy - 1), COLOR_WHITE)
        elif "hz_" in name or "hazard" in name:
            # Diamond hazard sign
            pts = [(cx, 2), (w - 3, cy), (cx, h - 3), (2, cy)]
            bg_col = (235, 75, 50) if "quake" in name or "fire" in name or "volcano" in name else (50, 140, 210)
            pygame.draw.polygon(surf, bg_col, pts)
            pygame.draw.polygon(surf, COLOR_OUTLINE, pts, 1)
            # Center symbol
            pygame.draw.line(surf, COLOR_WHITE, (cx, cy - 3), (cx, cy + 1), 1)
            surf.set_at((cx, cy + 3), COLOR_WHITE)
        else:
            pygame.draw.rect(surf, (215, 185, 135), (1, 1, w - 2, h - 2))
            pygame.draw.rect(surf, COLOR_OUTLINE, (1, 1, w - 2, h - 2), 1)

        return surf

    @classmethod
    def _generate_generic_block(cls, name: str, size: Tuple[int, int]) -> pygame.Surface:
        """Fallback simple pixel block with distinct border."""
        w, h = size
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        seed = sum((i + 1) * ord(c) for i, c in enumerate(name))
        r = (seed * 67) % 180 + 50
        g = (seed * 113) % 180 + 50
        b = (seed * 179) % 180 + 50
        pygame.draw.rect(surf, (r, g, b), (1, 1, w - 2, h - 2))
        pygame.draw.rect(surf, COLOR_OUTLINE, (0, 0, w, h), 1)
        return surf

    @classmethod
    def generate_world_map(cls, size: Tuple[int, int] = (320, 180)) -> pygame.Surface:
        """Create a clean storybook pixel-art archipelago world map placeholder."""
        w, h = size
        surf = pygame.Surface((w, h))
        # Deep blue sea background
        surf.fill((42, 86, 126))

        # Shallow reef water around islands
        reef_color = (68, 124, 162)

        # Island 1: Home Village & West Ridge (Left)
        pts_left = [(25, 90), (45, 60), (85, 55), (110, 80), (105, 140), (50, 155), (20, 130)]
        pygame.draw.polygon(surf, reef_color, [(x - 3, y - 3) for x, y in pts_left])
        pygame.draw.polygon(surf, COLOR_GRASS, pts_left)
        pygame.draw.polygon(surf, COLOR_SAND, pts_left, 2)

        # Island 2: Central Region & Mountain Ridge (Center)
        pts_mid = [(120, 70), (160, 40), (210, 45), (225, 105), (195, 145), (140, 135)]
        pygame.draw.polygon(surf, reef_color, [(x - 4, y - 4) for x, y in pts_mid])
        pygame.draw.polygon(surf, (108, 158, 88), pts_mid)
        pygame.draw.polygon(surf, COLOR_SAND, pts_mid, 2)
        # Mountain range in center
        pygame.draw.polygon(surf, (135, 120, 100), [(155, 95), (175, 65), (195, 95)])
        pygame.draw.polygon(surf, (155, 140, 120), [(175, 100), (190, 75), (205, 100)])

        # Island 3: Volcano & Plains (Right)
        pts_right = [(235, 50), (280, 35), (305, 75), (295, 130), (250, 140), (230, 95)]
        pygame.draw.polygon(surf, reef_color, [(x - 3, y - 3) for x, y in pts_right])
        pygame.draw.polygon(surf, (138, 142, 85), pts_right)
        pygame.draw.polygon(surf, COLOR_SAND, pts_right, 2)
        # Volcano peak
        pygame.draw.polygon(surf, (115, 85, 75), [(260, 85), (275, 55), (290, 85)])
        surf.set_at((275, 54), (235, 75, 45))  # Caldera glow

        # Dotted route paths connecting island checkpoints
        route_pts = [
            (40, 120),  # START / Home
            (70, 67),   # Stage 1 / Plateau
            (155, 90),  # Stage 2 / Central
            (135, 130), # Stage 3 / Harbor
            (260, 115), # Stage 4 / Plains
            (275, 75),  # Stage 5 / Volcano
            (185, 50),  # END / Mount Talon
        ]
        for i in range(len(route_pts) - 1):
            p1, p2 = route_pts[i], route_pts[i + 1]
            steps = 10
            for s in range(steps):
                t = s / steps
                rx = int(p1[0] + (p2[0] - p1[0]) * t)
                ry = int(p1[1] + (p2[1] - p1[1]) * t)
                if s % 2 == 0:
                    surf.set_at((rx, ry), (245, 230, 180))

        return surf

    @classmethod
    def generate_walk_sheet(cls, name: str, height: int = 24) -> pygame.Surface:
        """Generate a complete 4x4 walking spritesheet (down, left, right, up) with 4 walk frames each."""
        frame_w = max(12, int(height * 0.75))
        frame_h = height
        sheet = pygame.Surface((frame_w * 4, frame_h * 4), pygame.SRCALPHA)

        for row, direction in enumerate(("down", "left", "right", "up")):
            for col in range(4):
                # Generate base directional frame
                base = cls._generate_character_sprite(name, (frame_w, frame_h))
                # Add walking leg bobbing offset on odd frames
                if col in (1, 3):
                    # Bob head and body 1px down
                    bobbed = pygame.Surface((frame_w, frame_h), pygame.SRCALPHA)
                    bobbed.blit(base, (0, 1 if col == 1 else -1))
                    base = bobbed
                if direction == "left":
                    # Slight shift left
                    base = pygame.transform.flip(base, True, False)
                elif direction == "right":
                    # Facing right
                    pass
                elif direction == "up":
                    # Darken face/hair for back view
                    pygame.draw.rect(base, COLOR_HAIR_DARK, (frame_w // 4, 1, frame_w // 2, frame_h // 3))

                sheet.blit(base, (col * frame_w, row * frame_h))

        return sheet


# Singleton instance
asset_manager = AssetManager()
