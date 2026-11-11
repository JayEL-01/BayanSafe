"""Campaign and chapter progression for BayanSafe."""
from src.core.save_data import delete_save, load_save, write_save
from src.core.database import db_manager


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
        self.db_player_id = getattr(self, 'db_player_id', None)

    def is_unlocked(self, stage_id):
        norm = self.STAGE_ALIASES.get(stage_id, stage_id)
        return norm in self.unlocked or stage_id in self.unlocked

    def complete_stage(self, stage_id):
        norm = self.STAGE_ALIASES.get(stage_id, stage_id)
        if norm not in self.STAGE_ORDER:
            return
        self.completed.add(norm)
        self.completed.add(stage_id)
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
        entry.update({
            "player_id": player_id,
            "name": self.challenger_name or player_id,
            "hero": character.get("name", "Hero"),
            "attempts": best["attempts"],
            "best_time": best["best_time"],
            "score": best["best_score"],
        })
        board[player_id] = entry
        self.campaign_results[stage_id] = stats
        self.save()
        if db_manager.is_connected:
            self._sync_run_to_db(stage_id, stats)

    def stage_high_scores(self, stage_id):
        entries = self.high_scores.get(stage_id, {}).values()
        return sorted(entries, key=lambda entry: entry.get("score", 0), reverse=True)

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
        if getattr(self, "db_player_id", None):
            return self.db_player_id
        username = self.challenger_name or self.challenger_id or "BayanHero"
        char_id = self.character.get("id", "juan") if self.character else "juan"
        player = db_manager.get_or_create_player(username, character_id=char_id)
        if player:
            self.db_player_id = player["player_id"]
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
        write_save({
            "version": 4,
            "campaign_version": 4,
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

        self.records = data.get("records", {})
        self.high_scores = data.get("high_scores", {})
        self.difficulty = data.get("difficulty", "standard")
        self.campaign_results = data.get("campaign_results", {})
        self.final_decision = str(data.get("final_decision", ""))

        stage = data.get("current_stage", self.STAGE_ORDER[0])
        self.current_stage = stage if stage in self.unlocked else self.STAGE_ORDER[0]

        if self.character is None:
            return False
        if not self.challenger_id:
            self.challenger_id = f"PLAYER-{self.character['id'].upper()}"[:14]
            self.challenger_name = self.challenger_id
        return True

    def erase(self):
        self.reset()
        delete_save()
