"""Access the cropped pixel-art pieces supplied in the BayanSafe reference sheet."""
from functools import lru_cache
from pathlib import Path

import pygame
from src.entities.walk_sheet import WalkSheet


ART_DIR = Path(__file__).resolve().parents[2] / "assets" / "images" / "reference_art"
GAME_ART_DIR = Path(__file__).resolve().parents[2] / "assets" / "images" / "game_art"

_NPC_KEYS = {
    "lola teresa": "lola_teresa", "dr. mira santos": "dr_mira_santos",
    "rico dela cruz": "rico_dela_cruz", "mang lito": "mang_lito",
    "elena reyes": "dr_elena_reyes", "tito ramon": "tito_ramon",
    "elias voss": "dr_elias_voss", "paolo santos": "engr_paolo_santos",
    "aling rosa": "aling_rosa", "jun": "jun", "berto": "berto", "liza": "liza",
    "mayor cruz": "mayor_cruz", "nurse joy": "nurse_joy",
    "captain reyes": "captain_reyes", "capt. reyes": "captain_reyes",
    "sari": "sari", "kuya ben": "kuya_ben", "mila": "mila",
    "tatay pio": "tatay_pio", "rhea": "rhea",
}

_BUILDING_KEYS = {
    1: "house_small", 2: "house_large", 3: "school", 4: "town_hall",
    5: "hospital", 6: "evacuation_center", 7: "shop", 8: "farm_house",
    9: "fishing_hut", 10: "lighthouse", 11: "warehouse", 12: "police_station",
    13: "fire_station", 14: "research_facility", 15: "radio_tower",
    16: "tent_camp", 17: "shelter", 18: "ruins", 19: "bridge", 20: "dock",
    21: "house_small_damaged", 22: "house_large_damaged",
    23: "school_damaged", 24: "town_hall_damaged",
}


@lru_cache(maxsize=256)
def sprite(category, name):
    game_name = name
    if category == "buildings" and str(name).startswith("building_"):
        try:
            game_name = _BUILDING_KEYS.get(int(str(name).split("_")[-1]), name)
        except ValueError:
            pass
    path = GAME_ART_DIR / category / f"{game_name}.png"
    try:
        return pygame.image.load(str(path)).convert_alpha()
    except (OSError, pygame.error):
        path = ART_DIR / category / f"{name}.png"
        try:
            return pygame.image.load(str(path)).convert_alpha()
        except (OSError, pygame.error):
            return None


def scaled(category, name, size):
    source = sprite(category, name)
    if source is None:
        return None
    width, height = max(1, round(size[0])), max(1, round(size[1]))
    if source.get_size() == (width, height):
        return source
    return pygame.transform.scale(source, (width, height))


def character_sprite_for(name, identity=""):
    """Return the matching roster art, with civilians for story-only guests."""
    text = f"{name} {identity}".casefold()
    recurring = (
        ("lola teresa", "recurring_01"), ("dr. mira santos", "recurring_02"),
        ("rico dela cruz", "recurring_03"), ("mang lito", "recurring_04"),
        ("elena reyes", "recurring_05"), ("tito ramon", "recurring_06"),
        ("elias voss", "recurring_07"), ("paolo santos", "recurring_08"),
    )
    regional = (
        ("aling rosa", "regional_01"), ("jun", "regional_02"),
        ("berto", "regional_03"), ("liza", "regional_04"),
        ("mayor cruz", "regional_05"), ("nurse joy", "regional_06"),
        ("captain reyes", "regional_07"), ("sari", "regional_08"),
        ("kuya ben", "regional_09"), ("mila", "regional_10"),
        ("tatay pio", "regional_11"), ("rhea", "regional_12"),
    )
    for label, asset in recurring + regional:
        if label in text:
            key = next((key for key in _NPC_KEYS if key in text), None)
            if key:
                sheet = sprite("characters", _NPC_KEYS[key])
                if sheet:
                    return sheet.subsurface((0, 0, sheet.get_width() // 4,
                                             sheet.get_height() // 4)).copy()
            return sprite("characters", asset)
    seed = sum((index + 1) * ord(char) for index, char in enumerate(text))
    return sprite("characters", f"civilian_{seed % 18 + 1:02}")


def player_sprite(character_id):
    name = "maria" if str(character_id).casefold() == "maria" else "juan"
    return sprite("player_frames", f"{name}_0_0")


@lru_cache(maxsize=64)
def npc_walk_sheet_for(name, identity=""):
    """Load the matching four-direction walk animation from the supplied roster."""
    text = f"{name} {identity}".casefold()
    key = next((value for label, value in _NPC_KEYS.items() if label in text), None)
    if key:
        path = GAME_ART_DIR / "characters" / f"{key}.png"
        try:
            return WalkSheet(path, height=30, fps=7, mirror_right=False)
        except (OSError, pygame.error, ValueError):
            return None
    return None


def effect_frame(name, size, time_seconds=0.0, fps=8):
    """Get one frame from a four-frame effect strip, scaled with nearest pixels."""
    source = sprite("effects", name)
    if source is None:
        return None
    frame_width = source.get_width() // 4
    if frame_width < 1:
        return scaled("effects", name, size)
    frame = source.subsurface((int(time_seconds * fps) % 4 * frame_width,
                               0, frame_width, source.get_height()))
    target = (max(1, round(size[0])), max(1, round(size[1])))
    return frame if frame.get_size() == target else pygame.transform.scale(frame, target)
