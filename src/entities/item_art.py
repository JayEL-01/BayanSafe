from functools import lru_cache
from pathlib import Path

import pygame
from src.entities.reference_art import scaled


_ASSET_DIR = Path(__file__).resolve().parents[2] / "assets" / "images" / "ui"
_SPRITE_FILES = {
    "backpack": "bag_backpack.png",
    "flashlight": "bag_light.png",
    "first_aid": "bag_medkit.png",
    "radio": "bag_radio.png",
    "water": "bag_water.png",
}


@lru_cache(maxsize=None)
def _load_supply_sprite(kind):
    """Load the supplied pixel-art inventory icon once per game process."""
    filename = _SPRITE_FILES.get(kind)
    if not filename:
        return None
    return pygame.image.load(str(_ASSET_DIR / filename)).convert_alpha()


def _item_kind(item_id, item_name=""):
    """Classify mission-specific IDs by the actual item named in stage data."""
    text = f"{item_id} {item_name}".lower().replace("_", " ").replace("-", " ")
    if any(word in text for word in ("go bag", "backpack", "emergency kit")):
        return "backpack"
    if "flashlight" in text:
        return "flashlight"
    if any(word in text for word in ("first aid", "medkit", "medicine", "bandage")):
        return "first_aid"
    if "water" in text:
        return "water"
    if "radio" in text:
        return "radio"
    if "battery" in text or "backup cell" in text:
        return "battery"
    if "fire blanket" in text:
        return "fire_blanket"
    if "mask" in text or "respirator" in text:
        return "mask"
    if "goggles" in text or "eye protection" in text:
        return "goggles"
    if "keycard" in text or "key card" in text:
        return "keycard"
    if "key" in text:
        return "key"
    if any(word in text for word in (
            "research", "record", "document", "checklist", "map", "log",
            "transmission", "blueprint", "evidence")):
        return "documents"
    if "rope" in text:
        return "rope"
    if any(word in text for word in ("wrench", "tool", "component", "part", "relay")):
        return "tools"
    if "fuel" in text:
        return "fuel"
    if "food" in text or "meal" in text:
        return "food"
    return "supply"


def draw_item(surface, rect, item_id, color, item_name=""):
    """Draw the named guide item as a distinct world pickup icon."""
    x, y = rect.center
    pygame.draw.ellipse(surface, (20, 30, 28), (x - 5, y + 3, 10, 3))
    kind = _item_kind(item_id, item_name)
    pack_item = {
        "first_aid": "first_aid", "water": "water_bottle", "food": "food_pack",
        "flashlight": "flashlight", "radio": "radio", "mask": "gas_mask",
        "backpack": "backpack", "rope": "rope", "tools": "tool_kit",
        "documents": "research_log", "keycard": "key_card", "key": "key_card",
        "battery": "battery", "fuel": "fuel_can", "medicine": "medicine",
        "bandage": "bandage", "supply": "electronic_part",
        "fire_blanket": "bandage", "goggles": "gas_mask",
    }.get(kind)
    if pack_item:
        # Mission objects are small readable pickups, below the player's
        # 20px sprite height and close to the 8px collision footprint.
        art = scaled("items", pack_item, (12, 12))
        if art:
            surface.blit(art, art.get_rect(center=(x, y)))
            return
    reference_item = {
        "first_aid": 1, "water": 2, "food": 3, "flashlight": 4,
        "radio": 5, "mask": 6, "backpack": 7, "rope": 8,
        "tools": 9, "documents": 12, "keycard": 11, "key": 11,
        "battery": 14, "fuel": 17, "medicine": 15, "bandage": 16,
        "goggles": 6, "fire_blanket": 16, "supply": 13,
    }.get(kind, 13)
    art = scaled("items", f"item_{reference_item:02}", (12, 12))
    if art:
        surface.blit(art, art.get_rect(center=(x, y)))
        return
    sprite = _load_supply_sprite(kind)
    if sprite:
        surface.blit(sprite, sprite.get_rect(center=(x, y)))
    elif kind == "backpack":
        pygame.draw.rect(surface, tuple(color), (x - 5, y - 5, 10, 11))
        pygame.draw.rect(surface, (235, 225, 190), (x - 2, y - 3, 4, 5))
        pygame.draw.rect(surface, (40, 60, 45), (x - 6, y - 5, 12, 11), 1)
        pygame.draw.rect(surface, (80, 115, 85), (x - 7, y - 3, 2, 7))
    elif kind == "radio":
        pygame.draw.rect(surface, (45, 60, 75), (x - 6, y - 5, 12, 10))
        pygame.draw.line(surface, (220, 230, 235), (x + 3, y - 5), (x + 6, y - 10), 1)
        pygame.draw.rect(surface, (110, 205, 230), (x - 4, y - 3, 5, 3))
        pygame.draw.line(surface, (190, 200, 205), (x - 4, y + 2), (x + 4, y + 2), 1)
    elif kind == "water":
        pygame.draw.rect(surface, (85, 175, 235), (x - 4, y - 4, 8, 10))
        pygame.draw.rect(surface, (190, 230, 245), (x - 2, y - 7, 4, 3))
        pygame.draw.rect(surface, (235, 250, 255), (x - 2, y - 2, 2, 5))
    elif kind == "mask":
        pygame.draw.polygon(surface, tuple(color), [(x - 5, y - 2), (x + 5, y - 2), (x + 4, y + 4), (x - 4, y + 4)])
        pygame.draw.line(surface, (235, 240, 220), (x - 5, y - 1), (x - 8, y - 4), 1)
        pygame.draw.line(surface, (235, 240, 220), (x + 5, y - 1), (x + 8, y - 4), 1)
        pygame.draw.rect(surface, (70, 80, 70), (x - 2, y, 4, 2))
    elif kind == "first_aid":
        pygame.draw.rect(surface, tuple(color), (x - 6, y - 4, 12, 9))
        pygame.draw.rect(surface, (245, 245, 230), (x - 1, y - 3, 3, 7))
        pygame.draw.rect(surface, (245, 245, 230), (x - 3, y - 1, 7, 3))
        pygame.draw.rect(surface, (55, 65, 60), (x - 6, y - 4, 12, 9), 1)
    elif kind == "flashlight":
        pygame.draw.rect(surface, (230, 210, 95), (x - 6, y - 2, 10, 5))
        pygame.draw.polygon(surface, (250, 240, 160), [(x + 3, y - 4), (x + 8, y), (x + 3, y + 4)])
        pygame.draw.rect(surface, (70, 75, 65), (x - 6, y - 2, 10, 5), 1)
    elif kind == "goggles":
        pygame.draw.rect(surface, (225, 212, 159), (x - 7, y - 3, 14, 7))
        pygame.draw.rect(surface, (45, 73, 78), (x - 6, y - 2, 5, 5))
        pygame.draw.rect(surface, (45, 73, 78), (x + 1, y - 2, 5, 5))
        pygame.draw.line(surface, (72, 59, 48), (x - 2, y), (x + 2, y), 1)
        pygame.draw.line(surface, (72, 59, 48), (x - 7, y - 1), (x - 9, y - 3), 1)
        pygame.draw.line(surface, (72, 59, 48), (x + 7, y - 1), (x + 9, y - 3), 1)
    elif kind == "documents":
        pygame.draw.rect(surface, (232, 219, 177), (x - 6, y - 6, 12, 12))
        pygame.draw.rect(surface, (110, 82, 52), (x - 6, y - 6, 12, 12), 1)
        pygame.draw.line(surface, (129, 91, 55), (x - 3, y - 3), (x + 3, y - 3), 1)
        pygame.draw.line(surface, (129, 91, 55), (x - 3, y), (x + 3, y), 1)
        pygame.draw.line(surface, (129, 91, 55), (x - 3, y + 3), (x + 1, y + 3), 1)
    elif kind == "key":
        pygame.draw.circle(surface, (238, 194, 92), (x - 2, y - 1), 4, 2)
        pygame.draw.line(surface, (238, 194, 92), (x + 2, y + 2), (x + 8, y + 8), 3)
        pygame.draw.line(surface, (127, 86, 44), (x + 5, y + 6), (x + 7, y + 4), 1)
    elif kind == "keycard":
        pygame.draw.rect(surface, (54, 111, 139), (x - 7, y - 5, 14, 10), border_radius=1)
        pygame.draw.rect(surface, (221, 237, 223), (x - 4, y - 2, 5, 2))
        pygame.draw.circle(surface, (244, 205, 93), (x + 4, y + 2), 1)
    elif kind == "battery":
        pygame.draw.rect(surface, (71, 95, 79), (x - 6, y - 4, 12, 9))
        pygame.draw.rect(surface, (226, 201, 104), (x - 2, y - 6, 4, 2))
        pygame.draw.rect(surface, (125, 205, 133), (x - 4, y - 2, 8, 5))
        pygame.draw.rect(surface, (30, 50, 40), (x - 6, y - 4, 12, 9), 1)
    elif kind == "tools":
        pygame.draw.rect(surface, (54, 74, 71), (x - 6, y - 5, 12, 10))
        pygame.draw.rect(surface, (178, 143, 81), (x - 3, y - 2, 6, 4))
        for dx in (-4, 0, 4):
            pygame.draw.line(surface, (219, 192, 118), (x + dx, y - 7), (x + dx, y - 5), 1)
            pygame.draw.line(surface, (219, 192, 118), (x + dx, y + 5), (x + dx, y + 7), 1)
    elif kind == "fire_blanket":
        pygame.draw.rect(surface, (185, 56, 45), (x - 6, y - 4, 12, 8))
        pygame.draw.line(surface, (248, 202, 111), (x - 3, y - 2), (x + 3, y + 2), 2)
        pygame.draw.rect(surface, (77, 53, 43), (x - 6, y - 4, 12, 8), 1)
    elif kind == "rope":
        pygame.draw.circle(surface, (199, 165, 102), (x, y), 6, 2)
        pygame.draw.circle(surface, (123, 88, 54), (x, y), 3, 1)
        pygame.draw.line(surface, (199, 165, 102), (x + 4, y + 3), (x + 8, y + 6), 2)
    elif kind == "fuel":
        pygame.draw.rect(surface, (176, 76, 53), (x - 5, y - 5, 10, 11))
        pygame.draw.rect(surface, (229, 193, 114), (x - 2, y - 7, 4, 2))
        pygame.draw.rect(surface, (241, 208, 121), (x - 2, y - 2, 4, 4))
    elif kind == "food":
        pygame.draw.ellipse(surface, (194, 137, 69), (x - 6, y - 4, 12, 8))
        pygame.draw.ellipse(surface, (237, 197, 113), (x - 4, y - 3, 8, 5))
    elif kind == "supply":
        pygame.draw.rect(surface, tuple(color), (x - 6, y - 5, 12, 10))
        pygame.draw.rect(surface, (245, 227, 187), (x - 2, y - 3, 4, 6))
        pygame.draw.rect(surface, (48, 56, 49), (x - 6, y - 5, 12, 10), 1)
    else:
        pygame.draw.rect(surface, tuple(color), (x - 5, y - 5, 10, 10))
        pygame.draw.rect(surface, (245, 245, 230), (x - 1, y - 4, 2, 8))
        pygame.draw.rect(surface, (245, 245, 230), (x - 4, y - 1, 8, 2))
