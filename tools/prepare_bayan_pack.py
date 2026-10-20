"""Prepare the supplied BayanSafe reference sheets for direct game use."""
from collections import deque
from pathlib import Path

import pygame


ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "assets/images/bayan_pack"
OUT = ROOT / "assets/images/game_art"


def remove_border_color(image, tolerance=18, background=None):
    """Make only the edge-connected card color transparent."""
    image = image.convert_alpha()
    w, h = image.get_size()
    px = bytearray(pygame.image.tobytes(image, "RGBA"))
    points = ((0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1))
    counts = {}
    for x, y in points:
        i = (y * w + x) * 4
        color = tuple(px[i:i + 3])
        counts[color] = counts.get(color, 0) + 1
    bg = tuple(background) if background is not None else max(counts, key=counts.get)
    seen = bytearray(w * h)
    q = deque()

    def matches(x, y):
        i = (y * w + x) * 4
        return max(abs(px[i + c] - bg[c]) for c in range(3)) <= tolerance

    for x in range(w):
        for y in (0, h - 1):
            if matches(x, y):
                n = y * w + x
                seen[n] = 1
                q.append((x, y))
    for y in range(h):
        for x in (0, w - 1):
            if matches(x, y):
                n = y * w + x
                if not seen[n]:
                    seen[n] = 1
                    q.append((x, y))
    while q:
        x, y = q.popleft()
        px[(y * w + x) * 4 + 3] = 0
        for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
            if 0 <= nx < w and 0 <= ny < h:
                n = ny * w + nx
                if not seen[n] and matches(nx, ny):
                    seen[n] = 1
                    q.append((nx, ny))
    return pygame.image.frombytes(bytes(px), (w, h), "RGBA")


def trim(image):
    bounds = image.get_bounding_rect(min_alpha=8)
    return image.subsurface(bounds).copy() if bounds.w and bounds.h else image


def save(image, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    pygame.image.save(image, str(path))


def make_grid(frames, path):
    """Store four columns by four rows: down, left, right, up."""
    cell_w = max(frame.get_width() for frame in frames)
    cell_h = max(frame.get_height() for frame in frames)
    sheet = pygame.Surface((cell_w * 4, cell_h * 4), pygame.SRCALPHA)
    for i, frame in enumerate(frames):
        x = (i % 4) * cell_w + (cell_w - frame.get_width()) // 2
        y = (i // 4) * cell_h + (cell_h - frame.get_height()) // 2
        sheet.blit(frame, (x, y))
    save(sheet, path)


def extract_npcs():
    # Each GIF frame shows the full 5x4 roster; four frames per direction.
    names = [
        "lola_teresa", "dr_mira_santos", "rico_dela_cruz", "mang_lito", "dr_elena_reyes",
        "tito_ramon", "dr_elias_voss", "engr_paolo_santos", "aling_rosa", "jun",
        "berto", "liza", "mayor_cruz", "nurse_joy", "captain_reyes",
        "sari", "kuya_ben", "mila", "tatay_pio", "rhea",
    ]
    source_frames = [pygame.image.load(str(ROOT / "assets/images/sprite_frames/npc" / f"frame_{i:02}.png"))
                     for i in range(16)]
    directions = ("down", "right", "up", "left")
    row_bounds = ((32, 153), (185, 305), (335, 457), (485, 610))
    for person, name in enumerate(names):
        col, row = person % 5, person // 5
        cell = pygame.Rect(col * 124, row_bounds[row][0], 124, row_bounds[row][1] - row_bounds[row][0])
        frames = []
        for direction_row in range(4):
            for phase in range(4):
                frame_index = direction_row * 4 + phase
                frame = source_frames[frame_index].convert()
                crop = frame.subsurface(cell).copy().convert_alpha()
                crop = trim(remove_border_color(crop, 8, (232, 240, 226)))
                frames.append(crop)
        # Source GIF direction order is down, right, up, left. Game sheet is
        # down, left, right, up to match WalkSheet and preserve left/right art.
        ordered = []
        for direction in ("down", "left", "right", "up"):
            start = directions.index(direction) * 4
            ordered.extend(frames[start:start + 4])
        make_grid(ordered, OUT / "characters" / f"{name}.png")


def extract_effects():
    names = ("rain", "wind", "fire", "smoke", "explosion",
             "water_splash", "ash", "dust", "heal", "warning_signal",
             "lightning", "falling_debris", "cracks", "dialogue_icon", "interaction_icon")
    source_frames = [pygame.image.load(str(ROOT / "assets/images/sprite_frames/effects" / f"frame_{i:02}.png"))
                     for i in range(4)]
    for index, name in enumerate(names):
        row, col = divmod(index, 5)
        frames = []
        for phase in range(4):
            image = source_frames[phase].convert()
            crop = image.subsurface(pygame.Rect(col * 116, row * 126, 116, 126)).copy()
            # Labels are inside the bottom strip of the sample cells.
            crop = crop.subsurface((0, 0, 116, 102)).copy()
            # The frame gutters are darker than the blue effect-card fill.
            # Sample a known interior corner of the card to remove the actual
            # card background while preserving each effect's colored pixels.
            crop = trim(remove_border_color(crop, 22, (70, 100, 140)))
            frames.append(crop)
        fw = max(f.get_width() for f in frames)
        fh = max(f.get_height() for f in frames)
        sheet = pygame.Surface((fw * 4, fh), pygame.SRCALPHA)
        for phase, frame in enumerate(frames):
            sheet.blit(frame, (phase * fw + (fw - frame.get_width()) // 2,
                               fh - frame.get_height()))
        save(sheet, OUT / "effects" / f"{name}.png")


def extract_asset_preview():
    """Crop native atlas examples from the supplied asset pack infographic."""
    sheet = pygame.image.load(str(PACK / "Asset_Pack_preview.png")).convert()
    # Reference layout is designed on a 1088x2048 canvas and scaled in source.
    sx, sy = sheet.get_width() / 1088, sheet.get_height() / 2048

    def crop(box, category, name, tolerance=12):
        x, y, w, h = box
        rect = pygame.Rect(round(x * sx), round(y * sy), round(w * sx), round(h * sy))
        image = trim(remove_border_color(sheet.subsurface(rect).copy(), tolerance))
        save(image, OUT / category / f"{name}.png")

    # Character cells (source infographic coordinates; two idle + four walk).
    for character, y0 in (("juan", 99), ("maria", 502)):
        for row in range(5):
            for col in range(6):
                crop((21 + col * 52, y0 + row * 75, 44, 65), "player_frames",
                     f"{character}_{row}_{col}", 14)
    # 16px terrain samples (3x display), clipped inside their sample cards.
    tile_names = ("grass", "forest", "mountain", "beach", "water", "road",
                  "bridge", "river", "farmland", "rocky", "lava")
    tile_x = (19, 69, 119, 169, 254, 401, 447, 493, 643, 728, 788)
    for name, x in zip(tile_names, tile_x):
        crop((x, 923, 37, 34), "terrain", name, 10)
    # Item illustrations are individually centered in 50px cards.
    items = ("first_aid", "water_bottle", "food_pack", "flashlight", "radio", "gas_mask",
             "backpack", "rope", "tool_kit", "map", "key_card", "research_log",
             "electronic_part", "battery", "medicine", "bandage", "fuel_can",
             "notebook", "phone", "money", "power_core", "research_terminal")
    item_positions = [(22 + col * 51, 1309) for col in range(17)] + [(22 + col * 51, 1374) for col in range(5)]
    for name, (x, y) in zip(items, item_positions):
        crop((x, y, 42, 36), "items", name, 12)
    # Distinct normal/damaged structure pairs from the reference grid.
    names = ("house_small", "house_small_damaged", "house_large", "house_large_damaged",
             "school", "school_damaged", "town_hall", "town_hall_damaged", "hospital",
             "hospital_damaged", "evacuation_center", "evacuation_center_damaged", "shop",
             "shop_damaged", "farm_house", "farm_house_damaged", "fishing_hut",
             "fishing_hut_damaged", "lighthouse", "lighthouse_damaged", "warehouse",
             "warehouse_damaged", "police_station", "police_station_damaged", "fire_station",
             "fire_station_damaged", "research_facility", "research_facility_damaged",
             "radio_tower", "radio_tower_damaged", "tent_camp", "tent_camp_damaged",
             "shelter", "shelter_damaged", "ruins", "bridge", "dock")
    for i, name in enumerate(names):
        row, col = divmod(i, 13)
        # The 13-column building atlas uses an 80px card pitch and ~90px row
        # pitch on the 1088px reference layout. Crop the illustration area,
        # leaving enough margin for the widest roof and tallest tower.
        crop((20 + col * 80, 1480 + row * 90, 60, 66), "buildings", name, 12)


def main():
    pygame.init()
    pygame.display.set_mode((1, 1), pygame.HIDDEN)
    OUT.mkdir(parents=True, exist_ok=True)
    extract_npcs()
    extract_effects()
    extract_asset_preview()
    print(f"Prepared clean reference assets in {OUT}")


if __name__ == "__main__":
    main()
