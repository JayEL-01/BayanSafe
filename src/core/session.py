"""Campaign and chapter progression for BayanSafe."""
from src.core.save_data import delete_save, load_save, write_save
from src.core.database import db_manager
from src.core.score_system import ScoreSystem


class GameSession:
    STAGE_ORDER = [
        "prologue",
        "chapter_1",
        "chapter_2",
        "chapter_3",
        "chapter_4",
        "chapter_5",
        "final_mission",
    ]
    STAGE_ALIASES = {
        "chapter_01": "chapter_1",
        "chapter_02": "chapter_2",
        "chapter_03": "chapter_3",
        "chapter_04": "chapter_4",
        "chapter_05": "chapter_5",
    }

    def __init__(self):
        self.reset()

    def reset(self):
        saved_high_scores = getattr(self, "high_scores", {})
        if not isinstance(saved_high_scores, dict):
            saved_high_scores = {}
        self.character = None
        self.unlocked = {self.STAGE_ORDER[0]}
        self.completed = set()
        self.records = {}
        self.current_stage = self.STAGE_ORDER[0]
        self.difficulty = "standard"
        self.campaign_results = {}
        self.final_decision = ""
        self.challenger_id = ""
        self.challenger_name = ""
        self.high_scores = saved_high_scores
        self.db_player_id = None
        self._db_player_username = None

        # A new campaign always starts with a clean preparedness record.
        self.score_system = ScoreSystem()
        # Exact mission/step resume point for "Continue".
        self.current_level = {}
        self._resume_level_progress = False

    def is_unlocked(self, stage_id):
        norm = self.STAGE_ALIASES.get(stage_id, stage_id)
        return norm in self.unlocked or stage_id in self.unlocked

    # ------------------------------------------------------------------
    # Exact mission progress (Continue / restart support)
    # ------------------------------------------------------------------
    @staticmethod
    def _level_identity(chapter_id, level_id):
        return {"chapter_id": chapter_id, "level_id": level_id}

    def has_level_progress(self, chapter_id=None, level_id=None):
        """True when saved progress belongs to the requested mission."""
        data = self.current_level if isinstance(self.current_level, dict) else {}
        if not data:
            return False
        if chapter_id is not None and data.get("chapter_id") != chapter_id:
            return False
        if level_id is not None and data.get("level_id") != level_id:
            return False
        return bool(data.get("chapter_id") and data.get("level_id"))

    def begin_level(self, chapter_id, level_id, resume=False):
        """Prepare exact-progress state for a mission.

        ``resume=True`` keeps a matching saved checkpoint; every other entry
        starts a clean attempt. The return value tells the level whether it
        should restore its quest position.
        """
        restore = bool(resume and self.has_level_progress(chapter_id, level_id))
        if restore:
            self._resume_level_progress = True
        else:
            self.current_level = self._level_identity(chapter_id, level_id)
            self.current_level.update({
                "current_objective_idx": 0,
                "current_step_idx": 0,
                "completed": False,
            })
            self._resume_level_progress = False
            self.save()
        return restore

    def update_level_progress(self, current_objective_idx=None, current_step_idx=None, **extra):
        """Persist the active quest step of the current mission."""
        if not isinstance(self.current_level, dict) or not self.has_level_progress():
            return
        if current_objective_idx is not None:
            self.current_level["current_objective_idx"] = max(0, int(current_objective_idx))
        if current_step_idx is not None:
            self.current_level["current_step_idx"] = max(0, int(current_step_idx))
        if extra:
            self.current_level.update(extra)
        self.save()

    def clear_level_progress(self, chapter_id=None, level_id=None):
        """Forget a finished mission (or explicitly matched mission)."""
        if chapter_id is not None or level_id is not None:
            if not self.has_level_progress(chapter_id, level_id):
                return
        self.current_level = {}
        self._resume_level_progress = False
        self.save()

    def consume_level_resume(self):
        """Return and clear the one-shot restore request used by BaseLevel."""
        requested = bool(self._resume_level_progress)
        self._resume_level_progress = False
        return requested

    def resume_mission(self):
        """Return the (chapter, level) the Continue button should open."""
        from src.story.chapter_registry import STORY_SEQUENCE, mission_key
        data = self.current_level if isinstance(self.current_level, dict) else {}
        chapter_id, level_id = data.get("chapter_id"), data.get("level_id")
        if (chapter_id, level_id) in STORY_SEQUENCE:
            return chapter_id, level_id

        candidates = [(ch, lvl) for ch, lvl in STORY_SEQUENCE if ch == self.current_stage]
        if not candidates:
            candidates = list(STORY_SEQUENCE)
        for chapter_id, level_id in candidates:
            if mission_key(chapter_id, level_id) not in self.campaign_results:
                return chapter_id, level_id
        return candidates[0]

    def complete_stage(self, stage_id):
        norm = self.STAGE_ALIASES.get(stage_id, stage_id)
        if norm not in self.STAGE_ORDER:
            return
        self._record_chapter_run(norm)
        self.completed.add(norm)
        self.completed.add(stage_id)
        self.current_level = {}
        self._resume_level_progress = False
        index = self.STAGE_ORDER.index(norm)
        next_stage = None
        if index + 1 < len(self.STAGE_ORDER):
            next_stage = self.STAGE_ORDER[index + 1]
            self.unlocked.add(next_stage)
            self.current_stage = next_stage
        self.save()
        if db_manager.is_connected:
            self._sync_stage_to_db(norm, completed=True, next_stage=next_stage)

    def record_run(self, stage_id, stats, count_attempt=True):
        best = self.records.setdefault(
            stage_id, {"best_time": None, "best_score": 0, "perfect": False, "attempts": 0}
        )
        if count_attempt:
            best["attempts"] = int(best.get("attempts", 0)) + 1
            best["previous_best_score"] = int(best.get("best_score", 0))
            if best["best_time"] is None or stats.get("time", 0) < best["best_time"]:
                best["best_time"] = stats.get("time", 0)
            best["latest_score"] = int(stats.get("score", 0))
            best["best_score"] = max(best["best_score"], stats.get("score", 0))
            best["perfect"] = best["perfect"] or stats.get("perfect", False)
        else:
            best["latest_score"] = int(stats.get("score", 0))
            best["best_score"] = max(best.get("previous_best_score", 0), stats.get("score", 0))

        character = self.character or {}
        player_id = self.challenger_id or "PLAYER-0001"
        board = self.high_scores.setdefault(stage_id, {})
        old_entry = board.get(player_id, {})
        entry = dict(old_entry)
        score = int(stats.get("score", 0))
        is_new_best = score >= int(old_entry.get("score", -1))
        entry.update({
            "player_id": player_id,
            "name": self.challenger_name or player_id,
            "hero": character.get("name", "Hero"),
            "attempts": best["attempts"],
            # A fresh campaign resets this run's record but must never erase a
            # leaderboard score that was preserved from an earlier campaign.
            "score": max(int(old_entry.get("score", 0)), int(best["best_score"])),
        })
        old_time = old_entry.get("best_time")
        new_time = best["best_time"]
        entry["best_time"] = (new_time if new_time is not None
                              and (old_time is None or new_time < old_time) else old_time)
        if is_new_best:
            entry["score"] = best["best_score"]
            entry["perfect"] = bool(stats.get("perfect", False))
            for field in ("quests_done", "quests_total", "items_found",
                          "items_total", "max_score", "damage"):
                entry[field] = int(stats.get(field, 0))
        board[player_id] = entry
        self.campaign_results[stage_id] = stats
        self.save()
        if db_manager.is_connected:
            self._sync_run_to_db(stage_id, stats)

    @staticmethod
    def chapter_mission_keys(chapter_id):
        """Return the leaderboard keys of every mission inside a chapter."""
        from src.story.chapter_registry import MISSION_INFO
        return [mission["key"] for mission in MISSION_INFO
                if mission["chapter_id"] == chapter_id]

    def chapter_totals(self, chapter_id):
        """Aggregate the best recorded result of every mission in a chapter.

        Returns None until at least one mission in the chapter has a record.
        """
        keys = self.chapter_mission_keys(chapter_id)
        if not keys:
            return None
        totals = {
            "score": 0,
            "time": 0,
            "attempts": 0,
            "quests_done": 0,
            "quests_total": 0,
            "items_found": 0,
            "items_total": 0,
            "max_score": 0,
            "damage": 0,
            "missions_done": 0,
            "missions_total": len(keys),
            "perfect": True,
            "completed": True,
        }
        found = False
        for key in keys:
            record = self.records.get(key)
            stats = self.campaign_results.get(key) or {}
            if not record and not stats:
                totals["perfect"] = False
                continue
            found = True
            record = record or {}
            totals["missions_done"] += 1
            totals["score"] += int(record.get("best_score", stats.get("score", 0)))
            best_time = record.get("best_time")
            if best_time is None:
                best_time = stats.get("time", 0)
            totals["time"] += int(best_time or 0)
            totals["attempts"] += int(record.get("attempts", 0) or 0)
            for field in ("quests_done", "quests_total", "items_found",
                          "items_total", "max_score", "damage"):
                totals[field] += int(stats.get(field, 0))
            totals["perfect"] = (totals["perfect"]
                                 and bool(record.get("perfect", stats.get("perfect", False))))
        return totals if found else None

    def _record_chapter_run(self, chapter_id):
        """Record a whole-chapter total built from that chapter's mission runs."""
        totals = self.chapter_totals(chapter_id)
        if totals is None:
            return
        best = self.records.setdefault(
            chapter_id, {"best_time": None, "best_score": 0, "perfect": False, "attempts": 0}
        )
        best["attempts"] = int(best.get("attempts", 0)) + 1
        best["previous_best_score"] = int(best.get("best_score", 0))
        best["latest_score"] = totals["score"]
        best["best_score"] = max(int(best.get("best_score", 0)), totals["score"])
        if best.get("best_time") is None or totals["time"] < best["best_time"]:
            best["best_time"] = totals["time"]
        best["perfect"] = bool(best.get("perfect")) or totals["perfect"]
        best["missions_done"] = totals["missions_done"]
        best["missions_total"] = totals["missions_total"]

        character = self.character or {}
        player_id = self.challenger_id or "PLAYER-0001"
        board = self.high_scores.setdefault(chapter_id, {})
        old_entry = board.get(player_id, {})
        entry = dict(old_entry)
        is_new_best = int(best["best_score"]) >= int(old_entry.get("score", -1))
        entry.update({
            "player_id": player_id,
            "name": self.challenger_name or player_id,
            "hero": character.get("name", "Hero"),
            "attempts": int(old_entry.get("attempts", 0)) + 1,
            # Never let a weaker replay erase a preserved chapter total.
            "score": max(int(old_entry.get("score", 0)), int(best["best_score"])),
        })
        old_time = old_entry.get("best_time")
        new_time = best["best_time"]
        entry["best_time"] = (new_time if new_time is not None
                              and (old_time is None or new_time < old_time) else old_time)
        if is_new_best:
            entry.update({
                "perfect": best["perfect"],
                "missions_done": totals["missions_done"],
                "missions_total": totals["missions_total"],
                "quests_done": totals["quests_done"],
                "quests_total": totals["quests_total"],
                "items_found": totals["items_found"],
                "items_total": totals["items_total"],
                "max_score": totals["max_score"],
                "damage": totals["damage"],
            })
        else:
            entry.setdefault("perfect", False)
            entry.setdefault("missions_done", totals["missions_done"])
            entry.setdefault("missions_total", totals["missions_total"])
        board[player_id] = entry

    def backfill_chapter_records(self, completed=None):
        """Create chapter totals for campaigns finished before chapter boards existed."""
        chapters = self.completed if completed is None else completed
        if not isinstance(chapters, (set, list, tuple, frozenset)):
            chapters = ()
        changed = False
        for chapter_id in self.STAGE_ORDER:
            keys = self.chapter_mission_keys(chapter_id)
            if not keys:
                continue
            # Older saves may not flag the final mission as completed because
            # it used to jump straight to the ending, so infer completion from
            # the recorded missions as well.
            all_missions = all(key in self.records for key in keys)
            if chapter_id not in chapters and not all_missions:
                continue
            if chapter_id in self.records and self.high_scores.get(chapter_id):
                continue
            if self.chapter_totals(chapter_id) is None:
                continue
            self._record_chapter_run(chapter_id)
            changed = True
        return changed

    def stage_high_scores(self, stage_id):
        board = self.high_scores.get(stage_id, {})
        if not isinstance(board, dict):
            return []
        return sorted(board.values(), key=lambda entry: entry.get("score", 0), reverse=True)

    def campaign_summary(self):
        runs = list(self.campaign_results.values())
        if not runs:
            return {"points": 0, "score_rate": 0.0, "stages": 0, "stages_total": len(self.STAGE_ORDER)}
        points = sum(run.get("score", 0) for run in runs)
        return {
            "points": points,
            "stages": len(runs),
            "stages_total": len(self.STAGE_ORDER),
        }

    def _ensure_db_player(self):
        if not db_manager.is_connected:
            return None
        username = self.challenger_name or self.challenger_id or "BayanHero"
        if getattr(self, "db_player_id", None) and getattr(self, "_db_player_username", None) == username:
            return self.db_player_id
        char_id = self.character.get("id", "juan") if self.character else "juan"
        player = db_manager.get_or_create_player(username, character_id=char_id)
        if player:
            self.db_player_id = player["player_id"]
            self._db_player_username = username
            return self.db_player_id
        return None

    def _sync_stage_to_db(self, stage_id, completed=True, next_stage=None):
        p_id = self._ensure_db_player()
        if not p_id:
            return
        rec = self.records.get(stage_id, {})
        db_manager.record_stage_run(
            player_id=p_id,
            stage_id=stage_id,
            time_seconds=int(rec.get("best_time") or 0),
            score=int(rec.get("best_score") or 0),
            completed=completed,
            perfect=bool(rec.get("perfect")),
            next_stage_id=next_stage
        )

    def _sync_run_to_db(self, stage_id, stats):
        p_id = self._ensure_db_player()
        if not p_id:
            return
        next_stage = None
        if stage_id in self.STAGE_ORDER:
            idx = self.STAGE_ORDER.index(stage_id)
            if idx + 1 < len(self.STAGE_ORDER):
                next_stage = self.STAGE_ORDER[idx + 1]
        db_manager.record_stage_run(
            player_id=p_id,
            stage_id=stage_id,
            time_seconds=int(stats.get("time", 0)),
            score=int(stats.get("score", 0)),
            completed=bool(stats.get("completed", True)),
            perfect=bool(stats.get("perfect", False)),
            damage_taken=int(stats.get("damage", 0)),
            objectives_done=int(stats.get("quests_done", 0)),
            items_found=int(stats.get("items_found", 0)),
            next_stage_id=next_stage
        )

    def save(self):
        score_system = getattr(self, "score_system", None)
        write_save({
            "version": 5,
            "campaign_version": 5,
            "character_id": self.character.get("id") if self.character else None,
            "challenger_id": self.challenger_id,
            "challenger_name": self.challenger_name,
            "unlocked": [s for s in self.STAGE_ORDER if s in self.unlocked],
            "completed": [s for s in self.STAGE_ORDER if s in self.completed],
            "records": self.records,
            "current_stage": self.current_stage,
            "difficulty": self.difficulty,
            "campaign_results": self.campaign_results,
            "final_decision": getattr(self, "final_decision", ""),
            "high_scores": self.high_scores,
            "score_system": score_system.to_dict() if score_system else {},
            "current_level": self.current_level if isinstance(self.current_level, dict) else {},
        })
        if db_manager.is_connected:
            p_id = self._ensure_db_player()
            if p_id and self.character:
                db_manager.update_player_character(p_id, self.character.get("id", "juan"))

    def load(self, characters):
        data = load_save()
        if not data:
            return False
        by_id = {item["id"]: item for item in characters}
        self.character = by_id.get(data.get("character_id"))
        self.challenger_id = str(data.get("challenger_id", ""))[:14]
        self.challenger_name = str(data.get("challenger_name", self.challenger_id))[:14]

        saved_unlocked = data.get("unlocked", [])
        self.unlocked = {s for s in saved_unlocked if s in self.STAGE_ORDER}
        self.unlocked.add(self.STAGE_ORDER[0])

        saved_completed = data.get("completed", [])
        self.completed = {s for s in saved_completed if s in self.STAGE_ORDER}

        records = data.get("records", {})
        self.records = records if isinstance(records, dict) else {}
        high_scores = data.get("high_scores", {})
        self.high_scores = high_scores if isinstance(high_scores, dict) else {}
        self.difficulty = data.get("difficulty", "standard")
        campaign_results = data.get("campaign_results", {})
        self.campaign_results = campaign_results if isinstance(campaign_results, dict) else {}
        self.final_decision = str(data.get("final_decision", ""))

        stage = data.get("current_stage", self.STAGE_ORDER[0])
        self.current_stage = stage if stage in self.unlocked else self.STAGE_ORDER[0]

        # The preparation record drives the ending, so restore the exact
        # counters accumulated during the campaign.
        self.score_system = ScoreSystem()
        score_data = data.get("score_system", {})
        if isinstance(score_data, dict):
            try:
                self.score_system.from_dict(score_data)
            except (TypeError, ValueError):
                self.score_system = ScoreSystem()

        progress = data.get("current_level", {})
        self.current_level = dict(progress) if isinstance(progress, dict) else {}
        self._resume_level_progress = False

        if self.character is None:
            return False
        if not self.challenger_id:
            self.challenger_id = f"PLAYER-{self.character['id'].upper()}"[:14]
            self.challenger_name = self.challenger_id
        self.db_player_id = None
        self._db_player_username = None
        if db_manager.is_connected:
            self._ensure_db_player()
        if self.backfill_chapter_records():
            self.save()
        return True

    def erase(self):
        # Keep the leaderboard intact when a campaign is replaced. Read it back
        # from disk first in case this is a fresh launch, then merge anything
        # that only lives in memory.
        saved = load_save()
        persisted = saved.get("high_scores") if isinstance(saved, dict) else None
        self.reset()
        if isinstance(persisted, dict):
            for key, board in persisted.items():
                if not isinstance(board, dict):
                    continue
                current = self.high_scores.get(key)
                if not isinstance(current, dict):
                    current = {}
                    self.high_scores[key] = current
                for player_id, entry in board.items():
                    current.setdefault(player_id, entry)
        delete_save()
