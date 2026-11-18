"""Hard-coded, code-rendered pixel art for world objects.

Everything in this module is drawn from in-code pixel grids, so the game
keeps its zero-image-asset look. It is shared by:

* ``src/story/base_level.py`` - pickups (``_draw_pickups``) and the
  interactable objects / zones (``_draw_interactables``).
* ``src/maps/block_map.py`` - the map items the player walks over (the
  prologue Go-Bag essentials and the story props).

The palette uses single characters:

    k outline   w white   r red    o orange  y yellow
    g green     b blue    c cyan   s silver  d dark grey
    n brown     p skin

``ICONS`` holds 10x10 sprites. Missing names fall back to the Go-Bag so a
new pickup id can never crash a level mid-frame.
"""
from typing import Dict, Tuple

import pygame


# ----------------------------------------------------------------------
# Palette used by the pixel grids ('.' is transparent)
# ----------------------------------------------------------------------
PALETTE: Dict[str, Tuple[int, int, int]] = {
    "k": (24, 22, 32),     # outline
    "w": (240, 240, 236),  # white
    "r": (210, 52, 52),    # red
    "o": (240, 140, 40),   # orange
    "y": (245, 210, 70),   # yellow
    "g": (70, 180, 100),   # green
    "b": (60, 110, 200),   # blue
    "c": (110, 200, 230),  # cyan
    "s": (170, 176, 188),  # silver
    "d": (84, 88, 100),    # dark grey
    "n": (140, 90, 50),    # brown
    "p": (240, 190, 160),  # skin
}

DIM_OUTLINE = (30, 30, 40)
DIM_FILL = (70, 72, 84)

# Every icon is a 10 x 10 grid.
ICONS: Dict[str, list] = {
    # ---- protection / tools (existing art) --------------------------
    "mask": [
        "..........",
        "..........",
        ".kkkkkkkk.",
        "kwwwwwwwwk",
        "kwbbbbbbwk",
        "kwbbbbbbwk",
        "kwwwwwwwwk",
        ".kkkkkkkk.",
        "..........",
        "..........",
    ],
    "extinguisher": [
        "....kk....",
        "...ksskk..",
        "....kk.k..",
        "..kkkkkk..",
        "..krrrrk..",
        "..krwwrk..",
        "..krwwrk..",
        "..krrrrk..",
        "..krrrrk..",
        "..kkkkkk..",
    ],
    "flashlight": [
        "..........",
        "..........",
        ".kk.......",
        "kyyk.kkkk.",
        "kyywkddddk",
        "kyywkddddk",
        "kyyk.kkkk.",
        ".kk.......",
        "..........",
        "..........",
    ],
    "firstaid": [
        "..........",
        "...kkkk...",
        "..kssssk..",
        ".kkkkkkkk.",
        ".kwwrrwwk.",
        ".kwrrrrwk.",
        ".kwwrrwwk.",
        ".kwwrrwwk.",
        ".kkkkkkkk.",
        "..........",
    ],
    "battery": [
        "....kk....",
        "...kssk...",
        "..kkkkkk..",
        "..kgggwk..",
        "..kgggwk..",
        "..kyyywk..",
        "..kyyywk..",
        "..kyyywk..",
        "..kkkkkk..",
        "..........",
    ],
    "fuelcan": [
        "..........",
        "..kkk.....",
        ".k.rkkkkk.",
        ".krrrrrrrk",
        ".krwwwrrrk",
        ".krwwwrrrk",
        ".krrrrrrrk",
        ".krrrrrrrk",
        ".kkkkkkkkk",
        "..........",
    ],
    "hardhat": [
        "..........",
        "..........",
        "...kkkk...",
        "..kyyyyk..",
        ".kyywyyyk.",
        ".kyyyyyyk.",
        "kkkkkkkkkk",
        "kyyyyyyyyk",
        ".kkkkkkkk.",
        "..........",
    ],
    "megaphone": [
        "..........",
        "......kk..",
        ".....kook.",
        "..kkkkook.",
        ".kdddkook.",
        ".kdddkook.",
        "..kkkkook.",
        ".....kook.",
        "......kk..",
        "..........",
    ],
    "stick": [
        "...kkk....",
        "..knnnk...",
        "..kn.kn...",
        ".....kn...",
        ".....kn...",
        ".....kn...",
        ".....kn...",
        ".....kn...",
        ".....kk...",
        "..........",
    ],
    "radio": [
        "......k...",
        ".....k....",
        ".kkkkkkkk.",
        "kssssssssk",
        "kskkkkssrk",
        "ksddddsssk",
        "kskkkkssrk",
        "ksddddsssk",
        "kkkkkkkkkk",
        "..........",
    ],
    "generator": [
        "..........",
        ".kkkkkkkk.",
        "kyyyyyyyyk",
        "kykkkkkkyk",
        "kykddddkyk",
        "kykddddkyk",
        "kykkkkkkyk",
        "kyyyyyyyyk",
        ".kk....kk.",
        "..........",
    ],
    "gobag": [
        "..........",
        "...kkkk...",
        "..k....k..",
        ".kbbbbbbk.",
        ".kbbbbbbk.",
        ".kbkkkkbk.",
        ".kbbbbbbk.",
        ".kbbbbbbk.",
        ".kkkkkkkk.",
        "..........",
    ],
    "ramp": [
        "..........",
        "..........",
        "........kk",
        "......kkss",
        "....kkssss",
        "..kkssssss",
        "kkssssssss",
        "ksssssssss",
        "kkkkkkkkkk",
        "..........",
    ],
    "drybag": [
        "..........",
        "...kkkk...",
        "..k....k..",
        ".kooooook.",
        ".kooooook.",
        ".kokkkkok.",
        ".kooooook.",
        ".kooooook.",
        ".kkkkkkkk.",
        "..........",
    ],
    "book": [
        "..........",
        ".kkkkkkkk.",
        ".kwwwwwwk.",
        ".kwkkkkwk.",
        ".kwwwwwwk.",
        ".kwkkkkwk.",
        ".kwwwwwwk.",
        ".kkkkkkkk.",
        "..........",
        "..........",
    ],

    # ---- Go-Bag essentials & pickups --------------------------------
    "water": [
        "....kk....",
        "...kcck...",
        "...kcck...",
        "..kkkkkk..",
        "..kwwcck..",
        "..kwccbk..",
        "..kbccbk..",
        "..kbccbk..",
        "..kkkkkk..",
        "..........",
    ],
    "food": [
        "..........",
        "..kkkkkk..",
        ".kyyyyyyk.",
        ".kyonnoyk.",
        ".kyonnoyk.",
        ".kyyyyyyk.",
        ".kyonnoyk.",
        ".kyyyyyyk.",
        "..kkkkkk..",
        "..........",
    ],
    "babybag": [
        "..........",
        "...kkkk...",
        "..k....k..",
        ".kwwwwwwk.",
        ".kwccccwk.",
        ".kwkkkkwk.",
        ".kwccccwk.",
        ".kwwwwwwk.",
        ".kkkkkkkk.",
        "..........",
    ],
    "medpack": [
        "..........",
        "...kkkk...",
        "..k....k..",
        ".kwwwwwwk.",
        ".kwrwwrwk.",
        ".kwwrrwwk.",
        ".kwrwwrwk.",
        ".kwwwwwwk.",
        ".kkkkkkkk.",
        "..........",
    ],
    "whistle": [
        "..........",
        "..........",
        "..kkkkkk..",
        ".kssssssk.",
        ".kskkyykk.",
        ".kskkyyk..",
        ".kssssssk.",
        "..kkkkkk..",
        "..........",
        "..........",
    ],
    "key": [
        "..........",
        "..kkk.....",
        ".kyyyk....",
        ".kykyk....",
        "..kyk.....",
        "..kykkkk..",
        "...kyyyyk.",
        "...kyk....",
        "...kyk....",
        "..........",
    ],
    "documents": [
        "..........",
        ".kkkkkkk..",
        ".kwwwwwk..",
        ".kwkkkwk..",
        ".kwwwwwk..",
        ".kwkkkwk..",
        ".kwwwwwk..",
        ".kwwwwwk..",
        ".kkkkkkk..",
        "..........",
    ],
    "map": [
        "..........",
        ".kkkkkkkk.",
        ".kgg.gggk.",
        ".kg.gg.gk.",
        ".kggggggk.",
        ".kg.gg.gk.",
        ".kgg.gggk.",
        ".kggggggk.",
        ".kkkkkkkk.",
        "..........",
    ],

    # ---- Non-essential "trap" items ---------------------------------
    "trap_tv": [
        "..........",
        ".kkkkkkkk.",
        ".kddddddk.",
        ".kdccccdk.",
        ".kdccccdk.",
        ".kddddddk.",
        ".kkkkkkkk.",
        "...k..k...",
        "..kk..kk..",
        "..........",
    ],
    "jewelry": [
        "..........",
        "..........",
        "...kkkk...",
        "..kyyyyk..",
        "..kykkyk..",
        "..kyyyyk..",
        "...kyyk...",
        "....kk....",
        "..........",
        "..........",
    ],
    "game": [
        "..........",
        ".kkkkkkkk.",
        ".kddddddk.",
        ".kdgddgdk.",
        ".kddddddk.",
        ".kdkkkkdk.",
        ".kddddddk.",
        ".kkkkkkkk.",
        "..........",
        "..........",
    ],

    # ---- Interactable objects / scenery props -----------------------
    "sign": [
        "..kkkkkk..",
        ".kyyyyyyk.",
        ".kykkkkyk.",
        ".kyyyyyyk.",
        ".kykkkkyk.",
        ".kyyyyyyk.",
        ".kkkkkkkk.",
        "...kk.....",
        "...kk.....",
        "...kk.....",
    ],
    "drain": [
        "..........",
        ".kkkkkkkk.",
        ".kssssssk.",
        ".kkkkkkkk.",
        ".kssssssk.",
        ".kkkkkkkk.",
        ".kssssssk.",
        ".kkkkkkkk.",
        "..........",
        "..........",
    ],
    "roof": [
        "..........",
        "....kk....",
        "...krrk...",
        "..krrrrk..",
        ".krrrrrrk.",
        "krrrrrrrrk",
        "kkkkkkkkkk",
        ".kssssssk.",
        ".kkkkkkkk.",
        "..........",
    ],
    "zinc": [
        "..........",
        ".kkkkkkkk.",
        ".kssssssk.",
        ".ksskkssk.",
        ".kssssssk.",
        ".ksskkssk.",
        ".kssssssk.",
        ".ksskkssk.",
        ".kkkkkkkk.",
        "..........",
    ],
    "branch": [
        "..........",
        ".......gg.",
        "..kk..ggg.",
        ".knnkkggg.",
        "..knnkgg..",
        "...knnk...",
        "....knnk..",
        ".....knnk.",
        "......kk..",
        "..........",
    ],
    "canal": [
        "..........",
        ".kkkkkkkk.",
        ".kwwccbbk.",
        ".kccbbbbk.",
        ".kbbbbbbk.",
        ".kbbbbbbk.",
        ".kccbbbbk.",
        ".kwwccbbk.",
        ".kkkkkkkk.",
        "..........",
    ],
    "wire": [
        "..........",
        ".kk.......",
        "krrk......",
        "krrrrkkkk.",
        ".krrrrrrrk",
        "..krrrrrk.",
        "...kkkk...",
        "....rr....",
        "...r..r...",
        "..........",
    ],
    "registry": [
        "..........",
        "..kkkkkk..",
        "..kwwwwk..",
        "..kwkkwk..",
        "..kwwwwk..",
        "..kwkkwk..",
        "..kwwwwk..",
        "..kwwwwk..",
        "..kkkkkk..",
        "..........",
    ],
    "chairs": [
        "..........",
        "...kk.....",
        "..knnk....",
        "..knnk....",
        "..knnk....",
        ".kknnkk...",
        "knnnnnnk..",
        "knnnnnnk..",
        "kkkkkkkk..",
        "..........",
    ],
    "desk": [
        "..........",
        ".kkkkkkkk.",
        ".knnnnnnk.",
        ".knnnnnnk.",
        ".kkkkkkkk.",
        "..k....k..",
        "..k....k..",
        "..k....k..",
        "..kk..kk..",
        "..........",
    ],
    "crate": [
        "..........",
        ".kkkkkkkk.",
        ".knnnnnnk.",
        ".knkkkknk.",
        ".knnnnnnk.",
        ".knkkkknk.",
        ".knnnnnnk.",
        ".kkkkkkkk.",
        "..........",
        "..........",
    ],
    "valve": [
        "..........",
        "....kk....",
        "..kkrrkk..",
        ".krrrrrrk.",
        ".krkkkkrk.",
        ".krk..krk.",
        ".krkkkkrk.",
        ".krrrrrrk.",
        "..kkkkkk..",
        "..........",
    ],
    "stairs": [
        "..........",
        "........kk",
        "......kkkk",
        "....kkkkkk",
        "..kkkkkkkk",
        "kkkkkkkkkk",
        "ksssssssss",
        "kkkkkkkkkk",
        "..........",
        "..........",
    ],
    "rock": [
        "..........",
        "...kkkk...",
        "..kssssk..",
        ".ksssssssk",
        ".ksssssssk",
        "kssssssssk",
        "kssssssssk",
        "kkkkkkkkkk",
        "..........",
        "..........",
    ],
    "siren": [
        "..........",
        "...kkkk...",
        "..krrrrk..",
        ".krrrrrrk.",
        ".krrwwrrk.",
        ".krrwwrrk.",
        ".krrrrrrk.",
        "..kkkkkk..",
        "...kkkk...",
        "..........",
    ],
    "binoculars": [
        "..........",
        ".kkk..kkk.",
        ".kdk..kdk.",
        ".kdk..kdk.",
        ".kkkkkkkk.",
        ".kddddddk.",
        ".kddddddk.",
        ".kkkkkkkk.",
        "..........",
        "..........",
    ],
    "gate": [
        "..........",
        ".rrrrrrrr.",
        ".kkkkkkkk.",
        "....kk....",
        "....kk....",
        "....kk....",
        "....kk....",
        "...kkkk...",
        "..........",
        "..........",
    ],
    "fire": [
        "..........",
        "..........",
        "...kk.....",
        "..krrk....",
        "..krrkk...",
        ".kroorrk..",
        ".krooyrk..",
        ".kroyyyrk.",
        "..kyyyyk..",
        "...kkkk...",
    ],
}

# ``light`` is the readable pickup name used by several missions; the
# flashlight grid is the intended art and stays available under both names.
ICONS["light"] = ICONS["flashlight"]

_ICON_CACHE: Dict[Tuple[str, int, bool], pygame.Surface] = {}


def icon_surface(name: str, scale: int = 1, dim: bool = False) -> pygame.Surface:
    """Return a cached surface for icon *name* (scaled by an integer factor)."""
    scale = max(1, int(scale))
    key = (name, scale, dim)
    surf = _ICON_CACHE.get(key)
    if surf is not None:
        return surf
    # A missing icon must never crash a level mid-frame. New pickup ids can
    # opt into existing art later; until then they use the generic field bag.
    rows = ICONS.get(name, ICONS["gobag"])
    surf = pygame.Surface((len(rows[0]) * scale, len(rows) * scale), pygame.SRCALPHA)
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch == ".":
                continue
            if dim:
                color = DIM_OUTLINE if ch == "k" else DIM_FILL
            else:
                color = PALETTE[ch]
            surf.fill(color, (x * scale, y * scale, scale, scale))
    _ICON_CACHE[key] = surf
    return surf


def draw_icon(surface: pygame.Surface, name: str, center: Tuple[int, int],
              scale: int = 1, dim: bool = False) -> pygame.Rect:
    surf = icon_surface(name, scale, dim)
    rect = surf.get_rect(center=center)
    surface.blit(surf, rect)
    return rect


# ----------------------------------------------------------------------
# Name -> art mappings
# ----------------------------------------------------------------------
# Map-item ids used by ``BlockMap.add_item`` (the prologue Go-Bag items and
# the story props) mapped onto the pixel sprites above.
ITEM_ART: Dict[str, str] = {
    "gobag": "gobag",
    "water": "water",
    "food": "food",
    "firstaid": "firstaid",
    "flashlight": "flashlight",
    "radio": "radio",
    "keycard": "key",
    "key": "key",
    "log": "documents",
    "map": "map",
    "battery": "battery",
    "meds": "firstaid",
    "babybag": "babybag",
    "medpack": "medpack",
    # non-essential "trap" pickups in the prologue tutorial
    "tv": "trap_tv",
    "jewelry": "jewelry",
    "game": "game",
}

# A few missions reuse the same map-item id for different named objects.
# When the label is known it wins, so each object still gets its own sprite.
ITEM_LABEL_ART: Dict[str, str] = {
    "baby bag": "babybag",
    "med pack": "medpack",
    "meds": "firstaid",
    "medicine": "firstaid",
    "torch": "flashlight",
}

# Interactable keys *and* labels mapped onto the pixel sprites. Labels are
# stored lower-case. Unknown keys fall back to the nearest match, then to a
# generic crate, so every interactable gets a hard-coded sprite.
INTERACTABLE_ART: Dict[str, str] = {
    # signs / notices / lookouts
    "board": "sign", "advisory": "sign", "warning": "sign",
    "viewpoint": "binoculars", "road_probe": "sign",
    "submerged crown": "sign", "courtyard": "sign",
    "assembly courtyard": "sign",
    # water / drainage / cleared strips
    "drain": "drain", "canal": "canal", "dike_breach": "canal",
    "irrigation dike": "canal", "firebreak": "canal",
    "firebreak line": "canal",
    # roofs / sheets
    "roof": "roof", "zinc": "zinc",
    # vegetation / rock / slope
    "branch": "branch",
    "boulder_rubble": "rock", "fallen boulder": "rock",
    "fissure_ledge": "rock", "basalt ledge": "rock",
    "scree_path": "rock", "unstable scree": "rock",
    "crack_a": "rock", "crack_b": "rock", "tension crack": "rock",
    # cables / power lines
    "wire": "wire", "lines": "wire", "mooring lines": "wire",
    "conduit_terminal": "wire", "exposed conduit": "wire",
    "pole": "wire", "leaning pole": "wire",
    # radios / sirens / consoles
    "radio": "radio", "vhf radio": "radio", "radio_bench": "radio",
    "vhf transceiver": "radio", "siren": "siren",
    "siren_console": "siren", "acoustic siren": "siren",
    # machinery / valves / breakers
    "generator": "generator", "sensor_array": "generator",
    "gas sensor array": "generator", "bus_radiator": "generator",
    "bus radiator intake": "generator",
    "breaker": "valve", "circuit breaker": "valve",
    "valve": "valve", "fuel cut-off valve": "valve",
    "airlock_override": "valve", "airlock override": "valve",
    "manifold": "valve", "scram": "valve",
    # furniture / storage
    "registry": "registry", "desk": "desk", "chairs": "chairs",
    "locker": "crate", "life vest": "crate",
    "ramp_debris": "crate", "ramp debris": "crate",
    "harvest_rack": "crate", "grain sack rack": "crate",
    # gates / barriers
    "corral_gate": "gate", "livestock pen": "gate",
    "pdz_gate": "gate", "highway boom barrier": "gate",
    # stairs / ascents
    "stairs": "stairs", "cliff stairs": "stairs",
    "canyon_stairs": "stairs", "canyon ridge ascent": "stairs",
    # fire
    "fire": "fire",
    # respirator fit checks
    "rhea_fit": "mask", "rhea respiratory fit": "mask",
}


def item_art_name(item_id: str, label: str = "") -> str:
    """Return the sprite name for a ``BlockMap`` map-item id (and label).

    The prologue reuses the ``firstaid`` id for several distinct bags, so a
    label match is checked first (e.g. "BABY BAG" -> babybag sprite).
    """
    lab = (label or "").strip().lower()
    if lab in ITEM_LABEL_ART:
        return ITEM_LABEL_ART[lab]
    return ITEM_ART.get((item_id or "").strip().lower(), "gobag")


def interactable_art_name(key: str, label: str = "") -> str:
    """Return the sprite name for an interactable key/label pair."""
    k = (key or "").strip().lower()
    if k in INTERACTABLE_ART:
        return INTERACTABLE_ART[k]
    lab = (label or "").strip().lower()
    if lab in INTERACTABLE_ART:
        return INTERACTABLE_ART[lab]
    # Dynamic keys such as "wet_0" fall back to their prefix.
    base = k.split("_")[0]
    if base in INTERACTABLE_ART:
        return INTERACTABLE_ART[base]
    return "crate"
