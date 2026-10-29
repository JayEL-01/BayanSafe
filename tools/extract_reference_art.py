"""Extract individual visual references from the supplied concept sheets.

This is a one-time asset preparation utility. It crops the user's attached
reference sheet and removes only connected pale card backgrounds, preserving
the pixel-art outlines and internal highlights.
"""
from collections import deque
from pathlib import Path
import argparse

import pygame


def remove_connected_card_bg(image):
    image = image.convert_alpha()
    width, height = image.get_size()
    raw = bytearray(pygame.image.tobytes(image, "RGBA"))
    seen = bytearray(width * height)
    queue = deque()

    def pale(x, y):
        offset = (y * width + x) * 4
        r, g, b = raw[offset:offset + 3]
        # The reference cards use both cool blue-white and warm ivory paper.
        # Flood fill starts at the crop edges, so a broad pastel test removes
        # the card without cutting similarly colored details inside a sprite.
        high = max(r, g, b)
        low = min(r, g, b)
        return ((r >= 205 and g >= 200 and b >= 178 and high - low <= 92)
                or (r >= 165 and g >= 205 and b >= 210))

    for x in range(width):
        for y in (0, height - 1):
            if pale(x, y):
                index = y * width + x
                seen[index] = 1
                queue.append((x, y))
    for y in range(height):
        for x in (0, width - 1):
            if pale(x, y):
                index = y * width + x
                if not seen[index]:
                    seen[index] = 1
                    queue.append((x, y))
    while queue:
        x, y = queue.popleft()
        raw[(y * width + x) * 4 + 3] = 0
        for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
            if 0 <= nx < width and 0 <= ny < height:
                index = ny * width + nx
                if not seen[index] and pale(nx, ny):
                    seen[index] = 1
                    queue.append((nx, ny))
    return pygame.image.frombytes(bytes(raw), (width, height), "RGBA")


def crop_save(sheet, box, path, transparent=True, trim=True):
    crop = sheet.subsurface(pygame.Rect(box)).copy()
    if transparent:
        crop = remove_connected_card_bg(crop)
    if trim:
        bounds = crop.get_bounding_rect(min_alpha=8)
        if bounds.width and bounds.height:
            crop = crop.subsurface(bounds).copy()
    path.parent.mkdir(parents=True, exist_ok=True)
    pygame.image.save(crop, str(path))
    return crop


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("reference", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--effects-reference", type=Path)
    parser.add_argument("--structure-reference", type=Path)
    args = parser.parse_args()
    pygame.init()
    pygame.display.set_mode((1, 1), pygame.HIDDEN)
    sheet = pygame.image.load(str(args.reference)).convert()
    root = args.output
    # Map tile samples from the reference's top strip. Keep their natural colors.
    tiles = [
        ("grass", (344, 58, 24, 52)), ("forest", (394, 58, 24, 52)),
        ("mountain", (443, 58, 25, 52)), ("beach", (493, 58, 25, 52)),
        ("water", (543, 58, 25, 52)), ("road", (593, 58, 24, 52)),
        ("bridge", (643, 58, 24, 52)), ("river", (693, 58, 24, 52)),
        ("farmland", (743, 58, 24, 52)), ("rocky", (793, 58, 18, 52)),
    ]
    for name, box in tiles:
        crop_save(sheet, box, root / "terrain" / f"{name}.png", True, False)

    # Eight recurring NPCs, with card labels cropped away.
    for i in range(8):
        x = 650 + i * 81
        crop_save(sheet, (x + 8, 220, 62, 61), root / "characters" / f"recurring_{i+1:02}.png")
    # Twelve region-specific characters.
    for i in range(12):
        x = 647 + i * 54
        crop_save(sheet, (x + 3, 377, 48, 57), root / "characters" / f"regional_{i+1:02}.png")
    # Reusable townspeople row.
    for i in range(18):
        x = 656 + i * 35
        crop_save(sheet, (x, 518, 31, 49), root / "characters" / f"civilian_{i+1:02}.png")

    # Three rows of recognizable structures, excluding captions.
    structure_rows = ((191, 283), (296, 390), (405, 493))
    for row, (y0, y1) in enumerate(structure_rows):
        for col in range(8):
            x0 = 14 + col * 77
            crop_save(sheet, (x0 + 7, y0 + 2, 62, y1 - y0 - 10),
                      root / "buildings" / f"building_{row*8+col+1:02}.png")
    if args.structure_reference:
        structures = pygame.image.load(str(args.structure_reference)).convert()
        crop_save(structures, (997, 343, 56, 68), root / "buildings" / "building_06.png")

    # Two rows of item and story-object artwork.
    for row, y in enumerate((562, 647)):
        for col in range(10):
            x = 12 + col * 62
            crop_save(sheet, (x + 4, y + 2, 52, 58),
                      root / "items" / f"item_{row*10+col+1:02}.png")

    # Hazard panels; crop art only and leave labels in the UI.
    for i in range(7):
        x = 638 + i * 95
        crop_save(sheet, (x + 3, 653, 88, 64), root / "hazards" / f"hazard_{i+1:02}.png")

    # The reference's final mission art is an appropriate background for the
    # control-room story chapter, never for the island map or regular missions.
    for name, box in (("world_engine", (647, 1018, 222, 139)),
                      ("control_room", (873, 1018, 147, 139))):
        crop_save(sheet, box, root / "locations" / f"{name}.png", False, False)

    if args.effects_reference:
        effects = pygame.image.load(str(args.effects_reference)).convert()
        names = ("explosion", "fire", "smoke", "water_splash", "dust",
                 "rain", "wind", "lightning", "ash", "electricity")
        for index, name in enumerate(names):
            row, column = divmod(index, 5)
            x, y = 907 + column * 80, 593 + row * 78
            crop_save(effects, (x + 11, y + 12, 56, 43),
                      root / "effects" / f"{name}.png")

    print(f"Extracted reference sprites into {root}")


if __name__ == "__main__":
    main()
