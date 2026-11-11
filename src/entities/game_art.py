"""Load authentic characters, NPCs, buildings, items, and animations from game_art."""
from functools import lru_cache
from pathlib import Path
import pygame

from src.entities.walk_sheet import WalkSheet


GAME_ART_DIR = Path(__file__).resolve().parents[2] / "assets" / "images" / "game_art"

NPC_KEYS = {
    # Recurring main characters
    "lola teresa": "lola_teresa",
    "lola nena": "lola_teresa",
    "nanay luz": "lola_teresa",
    "lola": "lola_teresa",
    "dr. mira santos": "dr_mira_santos",
    "dr. mira": "dr_mira_santos",
    "lola pilar": "dr_mira_santos",
    "mira": "dr_mira_santos",
    "rico dela cruz": "rico_dela_cruz",
    "rico": "rico_dela_cruz",
    "mang lito": "mang_lito",
    "mang tomas": "mang_lito",
    "lito": "mang_lito",
    "elena reyes": "dr_elena_reyes",
    "dr. elena": "dr_elena_reyes",
    "tito ramon": "tito_ramon",
    "ramon": "tito_ramon",
    "elias voss": "dr_elias_voss",
    "dr. elias": "dr_elias_voss",
    "dr. voss": "dr_elias_voss",
    "paolo santos": "engr_paolo_santos",
    "engr. paolo": "engr_paolo_santos",
    "engr. rica": "engr_paolo_santos",
    "rica alvarez": "engr_paolo_santos",
    "tarsi lead": "engr_paolo_santos",
    "aling rosa": "aling_rosa",
    "aling marta": "aling_rosa",
    "rosa": "aling_rosa",
    "jun": "jun",
    "kuya jun": "jun",
    "kuya gary": "jun",
    "dock worker": "jun",
    "berto": "berto",
    "berting": "berto",
    "mang berting": "berto",
    "mang andoy": "berto",
    "mang kiko": "berto",
    "mang pido": "mang_lito",
    "liza": "liza",
    "nanay cora": "liza",
    "mayor cruz": "mayor_cruz",
    "kapitan jo": "mayor_cruz",
    "mayor": "mayor_cruz",
    "nurse joy": "nurse_joy",
    "nurse lorna": "nurse_joy",
    "nurse": "nurse_joy",
    "captain reyes": "captain_reyes",
    "captain dolor reyes": "captain_reyes",
    "dolor reyes": "captain_reyes",
    "capt. reyes": "captain_reyes",
    "tanod tomas": "captain_reyes",
    "kapitan ben": "kuya_ben",
    "kap. ben": "kuya_ben",
    "kuya ben": "kuya_ben",
    "ben": "kuya_ben",
    "sari": "sari",
    "pipoy": "sari",
    "injured boy": "sari",
    "missing boy": "sari",
    "sibling (radio)": "sari",
    "sibling": "sari",
    "stranded worker": "berto",
    "panicked shop owner": "mang_lito",
    "mila": "mila",
    "tatay pio": "tatay_pio",
    "pio": "tatay_pio",
    "rhea": "rhea",
    "tarsi": "rhea",
}


def _safe_load(path):
    surf = pygame.image.load(str(path))
    try:
        if pygame.display.get_surface() is not None:
            return surf.convert_alpha()
    except Exception:
        pass
    return surf


@lru_cache(maxsize=128)
def player_sprite(character_id, size=None):
    """Load the front-facing idle sprite for Juan or Maria from game_art/player_frames."""
    char = "maria" if "maria" in str(character_id).lower() else "juan"
    path = GAME_ART_DIR / "player_frames" / f"{char}_0_0.png"
    if not path.is_file():
        return None
    surf = _safe_load(path)
    if size and surf.get_size() != size:
        surf = pygame.transform.scale(surf, size)
    return surf


class GameArtPlayerSheet:
    """4-direction walking and idle animation for player using game_art/player_frames."""

    def __init__(self, character_id, height=24, fps=8):
        char = "maria" if "maria" in str(character_id).lower() else "juan"
        self.character = char
        self.fps = fps
        self.height = height
        width = max(1, round(height * 0.72))
        self.size = (width, height)
        self.facing = "down"
        self.timer = 0.0
        self.index = 0

        # rows: 0=down, 1=left, 2=right, 3=up
        # columns 2..5 are walking frames
        rows = {"down": 0, "left": 1, "right": 2, "up": 3}
        self.frames = {}
        for direction, row in rows.items():
            dir_frames = []
            for col in range(2, 6):
                path = GAME_ART_DIR / "player_frames" / f"{char}_{row}_{col}.png"
                if path.is_file():
                    img = _safe_load(path)
                    img = pygame.transform.scale(img, (width, height))
                    dir_frames.append(img)
            self.frames[direction] = dir_frames

        # idle pose (row 0, col 0)
        idle_path = GAME_ART_DIR / "player_frames" / f"{char}_0_0.png"
        if idle_path.is_file():
            idle_surf = _safe_load(idle_path)
            self.idle = pygame.transform.scale(idle_surf, (width, height))
        else:
            self.idle = self.frames["down"][0] if self.frames.get("down") else None

    def update(self, dt, dx, dy):
        if dx or dy:
            if abs(dx) > abs(dy) + 0.12:
                self.facing = "right" if dx > 0 else "left"
            elif abs(dy) > abs(dx) + 0.12:
                self.facing = "down" if dy > 0 else "up"
            self.timer += dt
            dir_frames = self.frames.get(self.facing, [])
            if dir_frames:
                self.index = int(self.timer * self.fps) % len(dir_frames)
        else:
            self.timer = 0.0
            self.index = 0

    def image(self):
        dir_frames = self.frames.get(self.facing, [])
        if self.timer <= 0:
            if self.facing == "down" and self.idle:
                return self.idle
            return dir_frames[0] if dir_frames else self.idle
        return dir_frames[self.index] if dir_frames else self.idle


def find_npc_key(name, identity=""):
    """Find matching character key in game_art/characters.

    Priority:
    1. NPC_KEYS lookup (name + identity text match)
    2. Direct id match against existing files in game_art/characters/
    3. None → caller falls back to procedural pixel art
    """
    text = f"{name} {identity}".lower()
    for term, key in NPC_KEYS.items():
        if term in text:
            return key
    # Try the raw id as a filename stem
    for candidate in (identity, name):
        stem = str(candidate).lower().replace(" ", "_").replace(".", "")
        path = GAME_ART_DIR / "characters" / f"{stem}.png"
        if path.is_file():
            return stem
    return None


@lru_cache(maxsize=64)
def npc_walk_sheet_for(name, identity="", height=27, fps=7):
    """Load 4x4 animated walking sheet for NPC from game_art/characters."""
    key = find_npc_key(name, identity)
    if not key:
        return None
    path = GAME_ART_DIR / "characters" / f"{key}.png"
    if not path.is_file():
        return None
    try:
        return WalkSheet(str(path), height=height, fps=fps, mirror_right=False)
    except Exception:
        return None


@lru_cache(maxsize=64)
def npc_portrait_for(name, identity="", size=None):
    """Get front-facing portrait or pose for NPC from game_art/characters."""
    key = find_npc_key(name, identity)
    if not key:
        return None
    path = GAME_ART_DIR / "characters" / f"{key}.png"
    if not path.is_file():
        return None
    try:
        sheet = _safe_load(path)
        fw, fh = sheet.get_width() // 4, sheet.get_height() // 4
        # row 0, col 0 is front-facing
        front = sheet.subsurface((0, 0, fw, fh)).copy()
        if size and front.get_size() != size:
            front = pygame.transform.scale(front, size)
        return front
    except Exception:
        return None


@lru_cache(maxsize=64)
def item_sprite(name, size=None):
    """Load item sprite from game_art/items."""
    path = GAME_ART_DIR / "items" / f"{name}.png"
    if not path.is_file():
        return None
    surf = _safe_load(path)
    if size and surf.get_size() != size:
        surf = pygame.transform.scale(surf, size)
    return surf


@lru_cache(maxsize=64)
def building_sprite(name, size=None):
    """Load building sprite from game_art/buildings."""
    path = GAME_ART_DIR / "buildings" / f"{name}.png"
    if not path.is_file():
        return None
    surf = _safe_load(path)
    if size and surf.get_size() != size:
        surf = pygame.transform.scale(surf, size)
    return surf


def effect_frame(name, size, time_seconds=0.0, fps=8):
    """Get frame from 4-frame strip in game_art/effects."""
    path = GAME_ART_DIR / "effects" / f"{name}.png"
    if not path.is_file():
        return None
    try:
        strip = _safe_load(path)
        fw = strip.get_width() // 4
        if fw < 1:
            return pygame.transform.scale(strip, size)
        frame = strip.subsurface((int(time_seconds * fps) % 4 * fw, 0, fw, strip.get_height()))
        return pygame.transform.scale(frame, size)
    except Exception:
        return None
