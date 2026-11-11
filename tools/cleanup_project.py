"""Project cleanup script — removes dead tool scripts, duplicate module roots,
and redundant asset folders that are never referenced by the actual game code.

Run from project root:  python tools/cleanup_project.py
"""
import shutil
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
deleted_files = []
deleted_dirs = []
errors = []

def del_file(rel):
    p = ROOT / rel
    if p.exists():
        try:
            p.unlink()
            deleted_files.append(rel)
            print(f"  DEL  {rel}")
        except Exception as e:
            errors.append(f"Could not delete {rel}: {e}")
            print(f"  ERR  {rel}: {e}")
    else:
        print(f"  SKIP {rel} (not found)")

def del_dir(rel):
    p = ROOT / rel
    if p.exists() and p.is_dir():
        try:
            shutil.rmtree(p)
            deleted_dirs.append(rel)
            print(f"  RMD  {rel}/")
        except Exception as e:
            errors.append(f"Could not remove {rel}: {e}")
            print(f"  ERR  {rel}/: {e}")
    else:
        print(f"  SKIP {rel}/ (not found)")


# =============================================================================
# 1. One-off tool scripts (all in tools/) — developed during session, not needed
# =============================================================================
print("\n=== Removing old tool scripts ===")
tool_scripts = [
    "tools/author_roster_dialogue.py",
    "tools/check_bayan_pack.py",
    "tools/check_hero_dims.py",
    "tools/check_npc_frames.py",
    "tools/check_npc_sheets.py",
    "tools/clean_image.py",
    "tools/cleanup_redundant_files.py",
    "tools/create_backup.py",
    "tools/extract_reference_art.py",
    "tools/generate_all_placeholders.py",
    "tools/generate_chapter_placeholders.py",
    "tools/generate_pixel_previews.py",
    "tools/patch_asset_candidates.py",
    "tools/patch_big_map.py",
    "tools/patch_prologue_sprites.py",
    "tools/patch_session.py",
    "tools/patch_world_map_state.py",
    "tools/prepare_bayan_pack.py",
    "tools/replace_chapter_placeholders.py",
    "tools/replace_legacy_art.py",
    "tools/replace_shared_placeholders.py",
    "tools/restore_world_map_json.py",
    "tools/restore_world_map_state.py",
    "tools/scaffold_modular_chapters.py",
    "tools/sync_user_sprites.py",
    "tools/update_world_map_json.py",
]
for s in tool_scripts:
    del_file(s)

# =============================================================================
# 2. Dead game-code files (never imported by any active module)
# =============================================================================
print("\n=== Removing dead game files ===")
dead_game_files = [
    "src/states/placeholder_state.py",
    "src/states/test_states.py",
    "src/core/placeholder_assets.py",
    "src/entities/character_scales.py",
]
for f in dead_game_files:
    del_file(f)

# =============================================================================
# 3. Root-level duplicate module trees (real code is in src/)
#    These self-reference themselves only; no actual game file imports from them.
# =============================================================================
print("\n=== Removing root-level duplicate module trees ===")
del_dir("server")
del_dir("core")
del_dir("config")
del_dir("world")
del_dir("database")

# =============================================================================
# 4. Redundant asset folders
# =============================================================================
print("\n=== Removing redundant asset folders ===")

# assets/shared/ — copies of images already in assets/images/
# Only referenced by asset_manager.py (which uses it as fallback),
# and no game code actually calls AssetManager — reference_art.py loads direct.
del_dir("assets/shared")

# assets/chapters/ — only tiny placeholder main_bg.png files (600 bytes each)
# referenced only by old tool scripts
del_dir("assets/chapters")

# assets/images/bayan_pack/ — GIF source files (extracted to sprite_frames/npc/)
del_dir("assets/images/bayan_pack")

# assets/images/menu/raw/ — raw pre-processed menu images, game uses processed ones
del_dir("assets/images/menu/raw")

# assets/storyscript/ — DOCX story script, not loaded by any code
del_dir("assets/storyscript")

# =============================================================================
# Summary
# =============================================================================
print(f"\n{'='*50}")
print(f"Deleted {len(deleted_files)} files, {len(deleted_dirs)} directories.")
if errors:
    print(f"ERRORS ({len(errors)}):")
    for e in errors:
        print(f"  {e}")
else:
    print("No errors.")
