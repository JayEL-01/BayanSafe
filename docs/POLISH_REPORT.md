# BayanSafe — Polish Pass Report

QA and polish pass over the full campaign (Prologue → Chapters 1–5 → Final Mission → Endings).
Story, lessons, level order and art are treated as frozen; `docs/STORY.md` is the source of truth.

- **Branch:** `polish-pass` (snapshot of the received state committed before any changes; `main` untouched)
- **Audit date:** 2026-11-11
- **Auditor:** automated code trace + headless play-simulation (see `tools/audit_text_overflow.py` and the reachability simulation below)

---

## 1. How to run

| What | Command (from the project root) |
|---|---|
| Play the game | `venv\Scripts\python.exe main.py` |
| Run the automated checks | `venv\Scripts\python.exe -m unittest discover -s tests` |
| Text-overflow audit helper | `venv\Scripts\python.exe tools\audit_text_overflow.py` |

- **Engine:** Python 3.14 + pygame-ce 2.5.8 (deps from `requirements.txt`; venv recreated during this audit — it was empty).
- **Rendering model:** 320×180 internal canvas, scaled ×4 to a 1280×720 window, 60 FPS. Plain colored blocks only (`src/config/palette.py`, `src/config/elements.py`); no environment images, as required.
- **Optional backend:** the Flask/PostgreSQL layer (`.env`, `src/core/database.py`) is not required to play; every call is guarded by `db_manager.is_connected`.

### Health check results

- All 12 unit tests pass (`test_story_rebuild`, `test_ui_layout`, `test_all_ui_theme`).
- The game boots headless for 8+ seconds with no errors on stdout/stderr.
- **However, the automated tests never simulate gameplay to completion** — they init/update/draw each level once. That is why the three progression blockers below were not caught.

---

## 2. Project map

### Entry & loop
- `main.py` → `Game` (`src/core/game.py`) → pushes `MainMenu`.
- `src/core/state_manager.py` — stack of states (`push`/`pop`/`change`).
- `src/core/session.py` — campaign progress (chapter-level granularity), save/load via `src/core/save_data.py` to `%LOCALAPPDATA%\BayanSafe\progress.json`.

### Story flow (verified end-to-end)
`MainMenu` → `CharacterSelect` (Juan/Maria + leaderboard ID) → `LoadingScreen` → `WorldMap` ("BEGIN THE JOURNEY") → `ChapterState` → `StoryLevelState` (`src/story/chapter_registry.py`) → the 25 levels:

- Prologue (San Isidro): tutorial, typhoon, flash flood, severe flooding — `src/story/prologue/`
- Chapter 1 North West Plateau: earthquake, landslide, calm wave, tsunami — `src/story/chapter_1/`
- Chapter 2 Central Town: fire, earthquake, typhoon, flash flood — `src/story/chapter_2/`
- Chapter 3 Harbor: flash flood, typhoon, severe flooding, fire+tsunami — `src/story/chapter_3/`
- Chapter 4 North East Plains: typhoon, flash flood, landslide, earthquake+volcano — `src/story/chapter_4/`
- Chapter 5 Volcano Valley: earthquake+landslide, volcano, flash fire, typhoon+severe flood — `src/story/chapter_5/`
- Final Mission: shutdown machine — `src/story/final_mission/shutdown_machine.py`
- Endings: 1 Complete Victory / 2 Partial Victory / 3 Total Failure — `src/story/endings/`

Level N completes → lesson modal → `advance_story()` → next level; chapter boundary → `session.complete_stage()` (unlocks next chapter, saves). Final mission → `launch_ending()` from the accumulated `ScoreSystem`.

### Core systems
- `src/story/base_level.py` — level engine (movement, NPCs, hazards, decisions, objectives/HUD, dialogue, lesson modal, legend, pause).
- `src/maps/block_map.py` — code-rendered colored environment (roads, water, buildings, hazard zones, safe zones, triggers, items).
- `src/hazards/` — typhoon (wind push + rain), earthquake (shake + debris), flash flood / severe flooding (rising water visuals), landslide / tsunami / flash fire / volcano (visuals).
- `src/core/score_system.py` — warnings followed, unsafe actions, residents assisted, evacuations, supplies; computes the ending.
- `src/core/decision_system.py` — safe/unsafe decision popups recorded into the score.
- `src/core/inventory_system.py` — go-bag items (**currently dead code — never instantiated**).
- `src/entities/player.py`, `npc.py`, `game_art.py` — player and NPC sprites (character art preserved under `assets/images/game_art/`).

### Configs
- `src/config/palette.py` — all environment colors. `src/config/elements.py` — element definitions. `src/config/cast.py` — character roles.
- `data/characters.json` — Juan/Maria stats and art paths. `data/world_map.json` — island map pages. `data/story/*.json` — chapter titles (only used by the High Scores screen). `data/guide.json`, `data/trivia.json` — guide/tip text.

---

## 3. Findings

### BLOCKERS (cannot progress)

**B1. Prologue Level 2 "Flash Flood" can never be completed.**
`src/story/prologue/level_2_flash_flood.py:46-48` — the river is a **full-height solid wall** (`add_water(310, 0, 70, 360)`). `add_bridge()` only draws a cosmetic rectangle; it does **not** open a gap in the water's collision rect (`src/maps/block_map.py:124-133`). Everything east of the river — NPC Berto (the level's decision) and the `flood_safe` safe-zone trigger (the level's win condition) — is unreachable. Player spawn is on the west bank. Since this is the **3rd of 25 levels** and progression is strictly linear, **the entire campaign stops here**. (Confirmed by a headless BFS over the real collision geometry: minimum distance from spawn to Berto is blocked entirely.)

**B2. Chapter 4 Level 2 "Flash Flood" can never be completed.**
Same root cause: `src/story/chapter_4/level_2_flash_flood.py:46` adds a full-height solid canal (`add_water(150, 0, 60, 360)`); the GRAIN TERMINAL safe zone (`terminal_safe`, line 53) is on the far side and unreachable. Objectives 1–2 are completable, objective 3 is impossible.

**B3. Chapter 5 Level 4 "Typhoon + Severe Flood" can never be completed.**
Same root cause: `src/story/chapter_5/level_4_typhoon_severe_flood.py:48` adds a full-height solid lahar channel (`add_water(160, 0, 90, 360)`); Mayor Cruz (the decision NPC) and the `ridge_safe` safe zone are unreachable.

**Fix plan (Phase 2):** make `add_bridge()` carve a walkable gap through water collision (bridge = crossable), matching the legend text "WOODEN BRIDGE — River crossing" and the story ("cross the wooden bridge", "follow remaining safe route"). This fixes all three levels with one change in the shared map builder, no per-level redesign needed.

---

### MAJOR (wrong state, broken scoring, missing screens)

**M1. Score carries over into a new game.** `GameSession.reset()` (`src/core/session.py:27-40`) never clears the dynamically-attached `score_system`. "START OVER" or "NEW GAME" in the same session reuses the previous campaign's warnings/unsafe counts, contaminating the next ending. `ScoreSystem` has no reset at all.

**M2. Score is never saved or loaded.** `ScoreSystem.to_dict()/from_dict()` exist (`src/core/score_system.py:82-102`) but are never called; `session.save()` omits the score. Quitting mid-campaign and pressing CONTINUE restores the chapter but starts a **fresh zero score**, so the ending is computed only from decisions made after the resume (and a zero-decision state defaults to a 100% preparedness ratio — a perfect ending for doing nothing).

**M3. Final Mission is never marked complete.** `FinalMissionShutdownMachine.proceed_to_next` (`src/story/final_mission/shutdown_machine.py:129-132`) jumps straight to `launch_ending`, bypassing `advance_story`'s end-of-sequence branch where `complete_stage("final_mission")` runs. Result: after finishing the game, CONTINUE replays the finale forever, and the main menu's "Your story is complete…" message (`src/states/main_menu.py:85-87`) can never appear.

**M4. Resuming always restarts the chapter from its first level.** The session stores only `current_stage` (chapter granularity). Quitting mid-chapter (or pause → WORLD MAP) resumes at that chapter's Level 1, losing up to 3 levels of progress. (`src/states/world_map.py:38-41` → `ChapterState.DEFAULT_LEVELS`, `src/states/chapter.py:19-32`.)

**M5. CONTINUE silently deletes the save file on load failure.** If the save parses but `character_id` can't be resolved, `session.load()` returns False and `MainMenu.continue_game` calls `session.erase()` with no message (`src/states/main_menu.py:91-93`). Destructive and invisible.

**M6. Decisions have no visible consequence.** After confirming a choice, the decision box vanishes instantly. The `recent_feedback`/`feedback_timer` (4 s) and the per-option `lesson` strings are stored (`src/core/decision_system.py:56-57, 79-89`) but **never rendered anywhere**. For an educational game the player gets zero feedback on safe vs unsafe choices. (Phase 2 spec: "Decision popups always have a safe and an unsafe choice with a visible consequence".)

**M7. Ending screens lack required elements.** All three endings are keyboard-only (`SPACE/ENTER/ESC` → Main Menu) — no **PLAY AGAIN** / **MAIN MENU buttons**, and the **educational note that the endings are fictional** (required by `docs/STORY.md`'s ending section and by the Phase 2 spec) is missing. `src/story/endings/ending_*.py:25-31`.

**M8. Chapter 4 Level 3 completes in one conversation.** Talking to Dr. Elena Reyes at *any* objective index calls `complete_objective()` three times plus `complete_level()` (`src/story/chapter_4/level_3_landslide.py:76-83`), skipping objectives 2–3 entirely; the level's own `seismo_safe` safe-zone trigger is never handled. Inconsistent with the standard completion pattern used by the other 21 levels.

**M9. Text overflows its boxes (measured).** Using the game's own font metrics (`tools/audit_text_overflow.py`):
- **45 of ~100 lesson lines** exceed the lesson modal's 270 px inner width (up to 333 px — past the 320 px canvas).
- **20 decision option lines** exceed the decision box's 264 px inner width (up to 302 px).
- **23 NPC dialogue lines** exceed the dialogue box's 288 px inner width (up to 339 px — past the canvas).
- **30 objective HUD lines** exceed the 220 px objective panel (up to 279 px).
- One lesson contains a broken degree sign (mojibake `+2?C`) in `src/story/chapter_2/level_3_typhoon.py`.

**M10. The go bag / inventory system is dead code.** `InventorySystem` is never instantiated; `session.inventory` never exists, so `BaseLevel.update`'s pickup branch (`src/story/base_level.py:204-206`) never runs; `supplies_secured` can only ever be 0; the story items (radio, data log, master key) have no effect; the tutorial's "collect Go-Bag supplies" objective is a map-collect only. Go-bag contents are part of the story (STORY.md Prologue).

**M11. Character choice is cosmetic in gameplay.** Every player is created with `speed=80` and no ability (`src/story/base_level.py:68-70`); the per-character stats and abilities (Juan sprint, Maria first aid — `data/characters.json`, documented in README) are never used. Also `walk_path` is built by formatting the whole character **dict** into a path string; it only works by accident because `Player.__init__` string-matches "maria" in the dict repr (`src/entities/player.py:19`).

**M12. "Escort" objectives don't escort.** The NPC follow/evacuate machinery (`src/entities/npc.py:94-184`: `evacuate()`, `start_following()`, `_plan_path()`, `update_following()`) is never called. Objectives that say "escort X to safety" are completed by the player walking alone while the NPC keeps wandering. (Phase 2 spec: "NPCs can be reached, talked to and escorted, and escort objectives count correctly".)

---

### MINOR (visual, text, feel)

1. **No fail/retry mechanic exists anywhere** — no timer that can expire, no health loss (`Player.take_damage` is dead), hazards never harm the player, and the `GameOver` state is unreachable. A careless player cannot fail a level. *(see "Needs my decision")*
2. **No movement tutorial hint** — the HUD shows `[ESC] Pause | [L] Legend | [SPACE] Interact` but never tells the player how to move (WASD/arrows). The tutorial level's objectives don't mention it either.
3. **Level transitions are instant** — lesson modal closes and the next level pops in with no fade ("Level complete" → lesson → next level exists, but the final hop is jarring).
4. **Typhoon wind pushes a standing player** — `get_wind_push()` is added to velocity unconditionally (`src/story/base_level.py:192-198`), so the player drifts ~15–30 px/s west/south even when not pressing keys.
5. **Earthquake expires after 12 s** (`src/hazards/earthquake.py:19`) — the level still calls itself an earthquake scenario after the shaking silently stops.
6. **ESC during an active decision opens the pause menu over it** (input priority order in `base_level.handle_input`), leaving the pending decision behind the menu.
7. **Tutorial objective text vs items mismatch** — objective says "(Water, Food, First Aid)" but the level requires 4 items including TORCH (`src/story/prologue/level_0_tutorial.py:33,62-65`).
8. **Legend is incomplete vs the palette** — no entries for commercial buildings, warehouses, damaged buildings, paths, or trees, which appear in levels; descriptions in `LEGEND_ENTRIES` are never drawn (only labels + swatches).
9. **High Scores screen** — chapter titles fall back to generic "Chapter N" because `data/story/chapter_01.json…chapter_04.json` use zero-padded names that don't match `chapter_1…chapter_5` (+ no files for chapter 5 / final mission); the local board can never populate because `session.record_run()` is never called; no mouse support on this screen.
10. **Leftover version/debug text** — "v0.1" on the main menu and footer; F2 debug overlay shipped; `print()` debug output on startup (`src/ui/backdrop.py:412-416`, `src/core/audio.py`, `theme.py:81`).
11. **README is stale** — describes the pre-rebuild architecture (22 stages, island exploration, M to view map, Q ability, mission prep screens, `HARDWARE_INTEGRATION.md` link that no longer exists); line 1 begins with a typo (`ye# BayanSafe`). Controls table lists keys the current game doesn't use (Q, H, M, Tab).
12. **Stray files** — repo-root `prefs.json` (never read; real prefs live in AppData), empty `saves/` directory, `src/states/big_map.py` + `BigMap` alias (dead), dead states `stage_complete.py`, `game_over.py`, `prologue.py` (all unreachable), dead `LoadingScreen(journey_map=True)` branch.
13. **Dead code in core** — `EventBus`/`Mascot` (never used), `record_run`/`campaign_summary` (never called), `session.difficulty`/`final_decision` (saved but never set), `Player.activate_ability`/`take_damage`/`invuln`, `ChapterState`'s unused `DialogueBox`/`ChoiceBox`/`paused` layer, `Decision.select()`.
14. **Broken dev tool** — `tools/test_session_sync.py` calls `complete_stage("earthquake")`, an id that isn't in `STAGE_ORDER`, so its assertions can never pass.
15. **Per-frame allocations** — `pygame.Surface((w,h), SRCALPHA)` created every frame in several draw paths (hazard zones, safe zones, overlays) and `surface.copy()` every shake frame; cheap at 320×180 but a known smell.
16. **Database module tries to connect at import** (3 s timeout when unreachable) which can delay game startup; stage ids seeded in the DB don't match the session's stage vocabulary.
17. **Pause menu is keyboard-only** although its docstring claims mouse support; story levels have no mouse support at all.
18. **High-scores screen mutates session state** directly from the save file.
19. `tests/theme_previews/*.png` are regenerated by the test run, so running the tests dirties the working tree (they differ run-to-run due to animation timing).

---

## 4. Needs my decision (not changed without your go-ahead)

1. **Prologue length:** your brief says "Prologue (2 levels)" but `docs/STORY.md` defines a tutorial **plus 3 levels** (Typhoon, Flash Flood, Severe Flooding), and the code implements 4. STORY.md is the stated source of truth, so I'll keep 4 unless you say otherwise.
2. **Fail/retry design:** there is currently *no way to fail a level* (no health, no timers, hazards are visual only, GameOver state is unreachable). Your Phase 2 asks for "a fail/retry path" and lists hazard timers (typhoon timer, tsunami wave timer). Adding failure/timers is a gameplay-design change (new mechanics), so I did not do it. Options: (a) leave as-is — score-only consequences; (b) add a light "restart level" option in the pause menu so a stuck player can retry (connects existing machinery, no new mechanic); (c) add real fail conditions (needs design work).
3. **Escort behavior:** wiring the existing NPC-follow machinery so escorted NPCs walk with the player (M12). It uses existing code, but it changes level pacing slightly (NPC must keep up / arrive with you).
4. **Character abilities (Q: Juan sprint / Maria first aid):** dead code today; README still documents them. Wire them up, or remove them from the README? (Wiring = restoring documented behavior; not wiring = README fix only.)
5. **Ending formula:** endings currently use only `warnings_followed`/`unsafe_actions`. STORY.md's ending conditions also mention residents assisted and supplies preserved. Changing the formula changes story outcomes — I'd keep the current thresholds unless you want assists/supplies weighed in.
6. **High scores:** `record_run()` exists but is never called, so the local leaderboard is always empty. Wire it (one call at level completion, using existing stats) or leave the board DB-only?
7. **Inventory/go bag (M10):** make collected items feed the (dead) InventorySystem so `supplies_secured` counts and the go bag persists between levels — or keep item pickup as level-local flavor?

---

## 5. Proposed Phase 2 scope (blockers + majors)

1. **B1–B3:** make bridges crossable (carve a gap in water collision) — one shared fix, unblocks the whole campaign.
2. **M1/M2:** reset + persist the score system with the save; restore on CONTINUE; default zero-decision ratio handled.
3. **M3:** mark the final mission complete when the ending launches, so CONTINUE shows the "story complete" message instead of replaying the finale.
4. **M4:** store the current level in the save and resume exactly where the player left off.
5. **M5:** show an on-screen message instead of silently erasing an unreadable save.
6. **M6:** render the decision feedback (safe/unsafe verdict + lesson line) for its 4-second window.
7. **M7:** add the fictional-endings note + working PLAY AGAIN / MAIN MENU buttons to all three ending screens.
8. **M8:** restore the standard objective flow in Chapter 4 Level 3 (decision completes 2 objectives, safe-zone trigger completes the level).
9. **M9:** wrap lesson/decision/dialogue/objective text to fit their boxes (shared helper in `base_level`), fix the mojibake character.
10. **M11:** use the selected character's real id for the sprite path (removes the dict-formatting fragility) without changing stats/abilities.
11. Regression: extend the test suite with a **full playthrough simulation** (auto-complete every level via its real win path) so blockers like B1–B3 can never come back silently.

Phase 3 will then cover the minor items (transitions/fades, controls hint, text wrap leftovers, typos, dead code removal, legend completion, README refresh).

---

*Phase 1 complete — waiting for your "go" before Phase 2.*
