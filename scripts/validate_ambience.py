import os
import sys
import time
import hashlib
import json
import random
import traceback

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
# ensure repo root on path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import pygame
from src.core import settings
from src.core.game import Game
from src.story.chapter_registry import STORY_SEQUENCE, load_level

pygame.init()
# Use the game's internal canvas size so rendering matches gameplay.
SCREEN_W, SCREEN_H = settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT
SCREEN = pygame.Surface((SCREEN_W, SCREEN_H))

CHAPTER_ORDER = ["prologue", "chapter_1", "chapter_2", "chapter_3", "chapter_4", "chapter_5", "final_mission"]
ARTIFACT_DIR = os.path.join(ROOT, "artifacts", "ambience")


def all_levels():
    return list(STORY_SEQUENCE)


def seed_all(seed=12345):
    random.seed(seed)
    try:
        import numpy as np  # optional
        np.random.seed(seed % (2**32 - 1))
    except Exception:
        pass


def make_game():
    g = Game()
    try:
        g.session.character = {"id": "juan", "name": "Juan"}
    except Exception:
        pass
    try:
        g.session.challenger_id = "VALIDATION"
        g.session.challenger_name = "VALIDATION"
    except Exception:
        pass
    try:
        if hasattr(g.session, "save"):
            # Avoid touching real save side effects during validation.
            g.session.save = lambda: None
    except Exception:
        pass
    try:
        # keep validation deterministic and quiet where possible
        if hasattr(g, "audio"):
            g.audio = None
    except Exception:
        pass
    return g


def load_lvl(ch, lv, ambience=True, seed=12345):
    seed_all(seed)
    g = make_game()
    st = load_level(g, ch, lv)
    level = st.level
    if not ambience:
        level.ambience = None
    # settle a couple of frames for deterministic start state
    for i in range(2):
        seed_all(seed + 100 + i)
        level.update(0.016)
        seed_all(seed + 200 + i)
        level.draw(SCREEN)
    return g, st, level


def surf_hash(surf):
    try:
        return hashlib.md5(pygame.image.tostring(surf, "RGB")).hexdigest()
    except Exception:
        return None


def rect_pixels(surf, rect):
    r = rect.clip(pygame.Rect(0, 0, surf.get_width(), surf.get_height()))
    if r.w <= 0 or r.h <= 0:
        return b""
    sub = surf.subsurface(r).copy()
    return pygame.image.tostring(sub, "RGBA")


def character_rects(level, surface):
    rects = []
    cam = getattr(level, "camera", None)
    p = getattr(level, "player", None)
    if p is not None and cam is not None:
        try:
            if hasattr(p, "sprite_screen_rect"):
                rects.append(("player", p.sprite_screen_rect(cam)))
            elif hasattr(p, "rect"):
                rects.append(("player", cam.apply(p.rect)))
        except Exception:
            pass
    for idx, npc in enumerate(getattr(level, "npcs", []) or []):
        try:
            name = getattr(npc, "name", f"npc_{idx}")
            if cam is not None and hasattr(npc, "sprite_screen_rect"):
                rects.append((name, npc.sprite_screen_rect(cam)))
            elif cam is not None and hasattr(npc, "rect"):
                rects.append((name, cam.apply(npc.rect)))
        except Exception:
            pass
    out = []
    bounds = pygame.Rect(0, 0, surface.get_width(), surface.get_height())
    for name, r in rects:
        try:
            rr = pygame.Rect(r).clip(bounds)
        except Exception:
            continue
        if rr.w > 0 and rr.h > 0:
            out.append((name, rr))
    return out


def dump_level_state(level):
    bm = getattr(level, "block_map", None)
    collisions = []
    if bm is not None:
        for r in getattr(bm, "collision_rects", []) or []:
            try:
                collisions.append([int(r.x), int(r.y), int(r.w), int(r.h)])
            except Exception:
                pass
    collisions = sorted(collisions)

    interactables = []
    for it in getattr(level, "interactables", []) or []:
        r = it.get("rect") if isinstance(it, dict) else getattr(it, "rect", None)
        if r is None:
            continue
        try:
            interactables.append({
                "key": it.get("key") if isinstance(it, dict) else getattr(it, "key", None),
                "label": it.get("label") if isinstance(it, dict) else getattr(it, "label", None),
                "rect": [int(r.x), int(r.y), int(r.w), int(r.h)],
                "near_inflate": [24, 24],
                "prompt": bool(it.get("prompt", True) if isinstance(it, dict) else getattr(it, "prompt", True)),
            })
        except Exception:
            pass
    interactables = sorted(interactables, key=lambda x: (str(x.get("key")), str(x.get("label")), x["rect"]))

    pickups = []
    for it in getattr(level, "pickups", []) or []:
        r = it.get("rect") if isinstance(it, dict) else getattr(it, "rect", None)
        if r is None:
            continue
        try:
            pickups.append({
                "key": it.get("key") if isinstance(it, dict) else getattr(it, "key", None),
                "rect": [int(r.x), int(r.y), int(r.w), int(r.h)],
                "source": "level_pickup",
            })
        except Exception:
            pass
    if bm is not None:
        for item in getattr(bm, "items", []) or []:
            r = getattr(item, "rect", None)
            if r is None:
                continue
            try:
                pickups.append({
                    "key": getattr(item, "item_id", getattr(item, "id", None)),
                    "rect": [int(r.x), int(r.y), int(r.w), int(r.h)],
                    "source": "map_item",
                })
            except Exception:
                pass
    pickups = sorted(pickups, key=lambda x: (str(x.get("source")), str(x.get("key")), x["rect"]))

    spawn = None
    p = getattr(level, "player", None)
    if p is not None and hasattr(p, "rect"):
        try:
            spawn = [int(p.rect.x), int(p.rect.y), int(p.rect.w), int(p.rect.h), int(p.rect.centerx), int(p.rect.centery)]
        except Exception:
            spawn = None
    elif p is not None and hasattr(p, "pos"):
        try:
            spawn = [int(p.pos[0]), int(p.pos[1])]
        except Exception:
            spawn = None

    npc_spawns = []
    for npc in getattr(level, "npcs", []) or []:
        try:
            npc_spawns.append({
                "name": getattr(npc, "name", None),
                "rect": [int(npc.rect.x), int(npc.rect.y), int(npc.rect.w), int(npc.rect.h)],
                "center": [int(npc.rect.centerx), int(npc.rect.centery)],
            })
        except Exception:
            pass
    npc_spawns = sorted(npc_spawns, key=lambda x: (str(x.get("name")), x.get("rect")))

    return {
        "collisions": collisions,
        "interactables": interactables,
        "pickups": pickups,
        "player_spawn": spawn,
        "npc_spawns": npc_spawns,
    }


def render_sequence(level, frames=60, dt=0.1):
    hashes = []
    snaps = []
    for i in range(frames):
        level.update(dt)
        level.draw(SCREEN)
        surf = SCREEN.copy()
        hashes.append(surf_hash(surf))
        if i in (0, 15, 30, 45, frames - 1):
            snaps.append((i, surf))
    return hashes, snaps


def contact_sheet(snaps, out_path, cols=5):
    if not snaps:
        return
    imgs = [s for _, s in snaps]
    rows = (len(imgs) + cols - 1) // cols
    w, h = imgs[0].get_size()
    sheet = pygame.Surface((cols * w, rows * h))
    sheet.fill((0, 0, 0))
    for idx, img in enumerate(imgs):
        r = idx // cols
        c = idx % cols
        sheet.blit(img, (c * w, r * h))
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    pygame.image.save(sheet, out_path)


def check_player_npc_pixels(ch, lv, steps=8, dt=0.1, seed=12345):
    g1, st1, l1 = load_lvl(ch, lv, ambience=False, seed=seed)
    g2, st2, l2 = load_lvl(ch, lv, ambience=True, seed=seed)
    diffs = []
    for step in range(steps):
        if step > 0:
            seed_all(seed + 1000 + step); l1.update(dt)
            seed_all(seed + 2000 + step); l1.draw(SCREEN); a = SCREEN.copy()
            seed_all(seed + 1000 + step); l2.update(dt)
            seed_all(seed + 2000 + step); l2.draw(SCREEN); b = SCREEN.copy()
        else:
            seed_all(seed + 2000 + step); l1.draw(SCREEN); a = SCREEN.copy()
            seed_all(seed + 2000 + step); l2.draw(SCREEN); b = SCREEN.copy()
        rects = character_rects(l1, a)
        if not rects:
            rects = character_rects(l2, b)
        for name, r in rects:
            pa = rect_pixels(a, r)
            pb = rect_pixels(b, r)
            if pa == pb:
                continue

            # If rect pixels differ, determine whether ambience drew over the
            # actual player/NPC sprites (bad) or only changed world/background
            # pixels visible through transparent parts of the sprite rect (ok).
            # Characters are drawn after under-ambience and before over-ambience;
            # so compare ambience-off vs ambience-on with all under-ambience
            # (ground/under/tint) suppressed. Equality there means no
            # over-ambience affected the sprite area.
            sprite_changed = True
            tint_only = False
            amb = getattr(l2, "ambience", None)
            if amb is not None:
                orig_tint = getattr(amb, "_tint_color_alpha", None)
                orig_ground = getattr(amb, "draw_ground", None)
                orig_under = getattr(amb, "draw_under", None)
                try:
                    if orig_tint is not None:
                        amb._tint_color_alpha = lambda: None
                    amb.draw_ground = lambda *args, **kwargs: None
                    amb.draw_under = lambda *args, **kwargs: None
                    seed_all(seed + 2000 + step); l2.draw(SCREEN); b_over_only = SCREEN.copy()
                    pb_over_only = rect_pixels(b_over_only, r)
                    if pa == pb_over_only:
                        sprite_changed = False
                        tint_only = True  # transparent/background area differs due to under-ambience/tint
                except Exception:
                    sprite_changed = True
                    tint_only = False
                finally:
                    if orig_tint is not None:
                        amb._tint_color_alpha = orig_tint
                    if orig_ground is not None:
                        amb.draw_ground = orig_ground
                    if orig_under is not None:
                        amb.draw_under = orig_under
                    # restore normal frame for subsequent steps/state consistency
                    seed_all(seed + 2000 + step); l2.draw(SCREEN)

            diffs.append({
                "chapter": ch, "level": lv, "step": step, "who": name,
                "rect": [r.x, r.y, r.w, r.h],
                "sprite_pixels_changed": sprite_changed,
                "transparent_bg_tint_only": tint_only,
            })
    return diffs


def measure_timing(ch, lv, ambience, warmup=10, runs=60, dt=0.1):
    _, _, level = load_lvl(ch, lv, ambience=ambience)
    for _ in range(warmup):
        level.update(dt)
        level.draw(SCREEN)
    times = []
    for _ in range(runs):
        t0 = time.perf_counter()
        level.update(dt)
        level.draw(SCREEN)
        t1 = time.perf_counter()
        times.append(t1 - t0)
    avg = sum(times) / len(times) if times else 0.0
    return avg, times


def hazard_reaction_check():
    targets = [
        ("final_mission", "shutdown_machine"),
        ("prologue", "level_3_severe_flooding"),
        ("chapter_2", "level_1_fire"),
        ("chapter_1", "level_1_earthquake"),
        ("prologue", "level_1_typhoon"),
    ]
    out = {}
    for ch, lv in targets:
        try:
            g, st, level = load_lvl(ch, lv, ambience=True)
            info = {"ok": True, "details": {}}
            amb = getattr(level, "ambience", None)
            info["details"]["ambience_enabled"] = amb is not None
            if amb is None:
                info["ok"] = False
                out[f"{ch}/{lv}"] = info
                continue
            flags = None
            try:
                from src.story.base_level import _hazard_flags
                flags = _hazard_flags(level)
            except Exception as e:
                info["details"]["flags_error"] = str(e)
            info["details"]["flags"] = flags
            hashes = []
            for _ in range(30):
                level.update(0.1)
                level.draw(SCREEN)
                hashes.append(surf_hash(SCREEN))
            info["details"]["animated"] = len(set(hashes)) > 1
            info["details"]["unique_hashes"] = len(set(hashes))
            if ch == "final_mission":
                info["details"]["has_terminals"] = len(getattr(amb, "_terminals", [])) > 0
            if flags:
                info["details"]["flood_flag"] = bool(flags.get("flood"))
                info["details"]["fire_flag"] = bool(flags.get("fire"))
                info["details"]["earthquake_flag"] = bool(flags.get("earthquake"))
                info["details"]["typhoon_flag"] = bool(flags.get("typhoon"))
            # target-specific sanity expectations
            if lv == "level_3_severe_flooding" and flags:
                info["ok"] = info["ok"] and bool(flags.get("flood"))
            if lv == "level_1_fire" and flags:
                info["ok"] = info["ok"] and bool(flags.get("fire"))
            if lv == "level_1_earthquake" and flags:
                info["ok"] = info["ok"] and bool(flags.get("earthquake"))
            if lv == "level_1_typhoon" and flags:
                info["ok"] = info["ok"] and bool(flags.get("typhoon"))
            out[f"{ch}/{lv}"] = info
        except Exception as e:
            out[f"{ch}/{lv}"] = {"ok": False, "error": str(e), "trace": traceback.format_exc()}
    return out


def heaviness(ch, lv):
    _, _, level = load_lvl(ch, lv, ambience=True)
    bm = getattr(level, "block_map", None)
    n = 0
    if bm is not None:
        n += len(getattr(bm, "elements", []) or [])
        n += len(getattr(bm, "items", []) or [])
        n += len(getattr(bm, "collision_rects", []) or [])
    n += len(getattr(level, "interactables", []) or [])
    n += len(getattr(level, "pickups", []) or [])
    n += len(getattr(level, "hazards", []) or [])
    n += len(getattr(level, "npcs", []) or [])
    amb = getattr(level, "ambience", None)
    if amb is not None:
        for attr in ("_windows", "_chimneys", "_trees", "_lamps", "_signs", "_terminals", "_pickups", "_birds", "_insects", "_fireflies", "_leaves", "_furniture"):
            n += len(getattr(amb, attr, []) or [])
    return n


def main():
    os.makedirs(ARTIFACT_DIR, exist_ok=True)
    levels = all_levels()
    print(f"Levels: {len(levels)}")

    chapter_anim = {}
    for ch in CHAPTER_ORDER:
        ch_levels = [lv for c, lv in levels if c == ch]
        rep = ch_levels[0] if ch_levels else None
        if rep is None:
            continue
        try:
            _, _, level = load_lvl(ch, rep, ambience=True)
            hashes, snaps = render_sequence(level, frames=60, dt=0.1)
            differs = len(set(hashes)) > 1
            sheet_path = os.path.join(ARTIFACT_DIR, f"contact_{ch}.png")
            contact_sheet(snaps, sheet_path)
            # save a few key frames for evidence
            key_frames = {}
            for idx, surf in snaps:
                fp = os.path.join(ARTIFACT_DIR, f"seq_{ch}_{rep}_f{idx:02d}.png")
                pygame.image.save(surf, fp)
                key_frames[str(idx)] = fp
            chapter_anim[ch] = {
                "representative_level": rep,
                "frames": 60,
                "differs_over_time": differs,
                "unique_hashes": len(set(hashes)),
                "contact_sheet": sheet_path,
                "key_frames": key_frames,
            }
            print(f"[anim] {ch}/{rep}: differs={differs} unique={len(set(hashes))}")
        except Exception as e:
            chapter_anim[ch] = {"error": str(e), "trace": traceback.format_exc()}
            print(f"[anim] {ch} error: {e}")

    pixel_diffs = []
    pixel_tint_only = []
    for ch, lv in levels:
        try:
            diffs = check_player_npc_pixels(ch, lv)
            sprite_changed = [d for d in diffs if d.get("sprite_pixels_changed")]
            tint_only = [d for d in diffs if d.get("transparent_bg_tint_only")]
            if sprite_changed:
                pixel_diffs.extend(sprite_changed)
                print(f"[pixels] SPRITE-DIFF {ch}/{lv}: {len(sprite_changed)} (tint-only-bg={len(tint_only)})")
            elif tint_only:
                pixel_tint_only.extend(tint_only)
                print(f"[pixels] OK {ch}/{lv} (sprite unchanged; transparent-bg tint diffs in rects={len(tint_only)})")
            else:
                print(f"[pixels] OK {ch}/{lv}")
        except Exception as e:
            err = {"chapter": ch, "level": lv, "error": str(e), "trace": traceback.format_exc(), "sprite_pixels_changed": True}
            pixel_diffs.append(err)
            print(f"[pixels] ERR {ch}/{lv}: {e}")

    timing = {}
    try:
        scores = []
        for ch, lv in levels:
            try:
                scores.append((heaviness(ch, lv), ch, lv))
            except Exception as e:
                print(f"[timing-heaviness] ERR {ch}/{lv}: {e}")
        scores.sort(reverse=True)
        heaviest = (scores[0][1], scores[0][2]) if scores else levels[-1]
        chH, lvH = heaviest
        print(f"[timing] heaviest: {chH}/{lvH} score={scores[0][0] if scores else 'n/a'}")
        avg_b, _ = measure_timing(chH, lvH, ambience=False, warmup=10, runs=60, dt=0.1)
        avg_a, _ = measure_timing(chH, lvH, ambience=True, warmup=10, runs=60, dt=0.1)
        delta_pct = ((avg_a - avg_b) / avg_b * 100.0) if avg_b else None
        timing = {
            "level": {"chapter": chH, "level": lvH},
            "avg_before_s": avg_b,
            "avg_after_s": avg_a,
            "delta_pct": delta_pct,
            "runs": 60,
            "warmup": 10,
        }
        if delta_pct is not None:
            print(f"[timing] before={avg_b:.6f}s after={avg_a:.6f}s delta={delta_pct:.2f}%")
        else:
            print(f"[timing] before={avg_b:.6f}s after={avg_a:.6f}s delta=n/a")
    except Exception as e:
        timing = {"error": str(e), "trace": traceback.format_exc()}
        print(f"[timing] error: {e}")

    state_diffs = []
    states = {}
    for ch, lv in levels:
        try:
            _, _, l1 = load_lvl(ch, lv, ambience=False)
            _, _, l2 = load_lvl(ch, lv, ambience=True)
            s1 = dump_level_state(l1)
            s2 = dump_level_state(l2)
            key = f"{ch}/{lv}"
            states[key] = {"before": s1, "after": s2}
            if s1 != s2:
                state_diffs.append({"level": key, "before": s1, "after": s2})
                print(f"[state] DIFF {key}")
            else:
                print(f"[state] OK {key}")
        except Exception as e:
            key = f"{ch}/{lv}"
            state_diffs.append({"level": key, "error": str(e), "trace": traceback.format_exc()})
            print(f"[state] ERR {key}: {e}")

    try:
        hazards = hazard_reaction_check()
    except Exception as e:
        hazards = {"error": str(e), "trace": traceback.format_exc()}

    report = {
        "canvas": {"width": SCREEN_W, "height": SCREEN_H},
        "chapter_animation": chapter_anim,
        "player_npc_sprite_pixel_diffs_count": len(pixel_diffs),
        "player_npc_sprite_pixel_diffs": pixel_diffs,
        "player_npc_transparent_bg_tint_only_count": len(pixel_tint_only),
        "player_npc_transparent_bg_tint_only": pixel_tint_only,
        "timing_heaviest": timing,
        "state_diffs_count": len(state_diffs),
        "state_diffs": state_diffs,
        "states_dump": states,
        "hazard_reactions": hazards,
    }
    out_path = os.path.join(ARTIFACT_DIR, "validation_report.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)

    # also write a compact states dump separately for easier inspection
    states_path = os.path.join(ARTIFACT_DIR, "level_states_dump.json")
    with open(states_path, "w", encoding="utf-8") as f:
        json.dump(states, f, indent=2, default=str)

    print(f"Report written: {out_path}")
    print(f"States written: {states_path}")
    print(f"Sprite pixel diffs: {len(pixel_diffs)}  Transparent-bg tint-only rect diffs: {len(pixel_tint_only)}  State diffs: {len(state_diffs)}")


if __name__ == "__main__":
    main()
