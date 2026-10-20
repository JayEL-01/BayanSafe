"""Campaign progress. The save file is local-first; hardware sync can mirror it later."""
from src.core.save_data import delete_save, load_save, write_save


class GameSession:
    STAGE_ORDER = [
        "home_island_tutorial",
        "earthquake",
        "landslide",
        "calm_before_wave",
        "tsunami",
        "flash_fire",
        "central_earthquake",
        "central_typhoon",
        "central_flash_flood",
        "harbor_flash_flood",
        "harbor_typhoon",
        "harbor_severe_flood",
        "harbor_fire_tsunami",
        "plains_typhoon",
        "plains_severe_flood",
        "plains_landslide",
        "plains_quake_volcano",
        "silence_volcano",
        "facility_fire",
        "volcano_flash_flood",
        "final_typhoon_flood",
        "final_shutdown",
    ]
    STAGE_ALIASES = {"central_landslide": "central_earthquake"}

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
        self.prep_choice = "route_plan"
        self.campaign_results = {}
        self.final_decision = ""
        self.challenger_id = ""
        self.challenger_name = ""
        self.high_scores = saved_high_scores

    def is_unlocked(self, stage_id):
        return stage_id in self.unlocked

    def complete_stage(self, stage_id):
        if stage_id not in self.STAGE_ORDER:
            return
        self.completed.add(stage_id)
        index = self.STAGE_ORDER.index(stage_id)
        if index + 1 < len(self.STAGE_ORDER):
            self.unlocked.add(self.STAGE_ORDER[index + 1])
            self.current_stage = self.STAGE_ORDER[index + 1]
        self.save()

    def record_run(self, stage_id, stats, count_attempt=True):
        best = self.records.setdefault(
            stage_id, {"best_time": None, "best_score": 0, "perfect": False, "attempts": 0}
        )
        if count_attempt:
            best["attempts"] = int(best.get("attempts", 0)) + 1
            best["previous_best_score"] = int(best.get("best_score", 0))
            if best["best_time"] is None or stats["time"] < best["best_time"]:
                best["best_time"] = stats["time"]
            best["latest_score"] = int(stats["score"])
            best["best_score"] = max(best["best_score"], stats["score"])
            best["perfect"] = best["perfect"] or stats["perfect"]
        else:
            # A wrong end-of-mission answer revises the current run. It is a
            # score penalty, not another gameplay attempt.
            best["latest_score"] = int(stats["score"])
            best["best_score"] = max(best.get("previous_best_score", 0), stats["score"])
        character = self.character or {}
        player_id = self.challenger_id or "PLAYER-0001"
        board = self.high_scores.setdefault(stage_id, {})
        old_entry = board.get(player_id, {})
        entry = dict(old_entry)
        stat_details = {key: int(stats.get(key, 0))
                        for key in ("quests_done", "quests_total", "items_found", "items_total")}
        if count_attempt:
            if int(stats["score"]) > int(old_entry.get("score", -1)):
                entry["previous_best_score"] = int(old_entry.get("score", 0))
                entry["previous_best_attempt"] = int(old_entry.get("best_attempt", 0))
                entry["previous_best_details"] = {
                    key: old_entry.get(key, 0) for key in stat_details
                }
                entry["best_attempt"] = best["attempts"]
                entry["score"] = int(stats["score"])
                entry.update(stat_details)
            entry.update({
                "player_id": player_id,
                "name": self.challenger_name or player_id,
                "hero": character.get("name", "Hero"),
                "attempts": best["attempts"],
                "best_time": best["best_time"],
            })
            board[player_id] = entry
        elif entry.get("best_attempt") == best["attempts"]:
            previous_score = int(entry.get("previous_best_score", 0))
            revised_score = int(stats["score"])
            if revised_score < previous_score:
                entry["score"] = previous_score
                entry["best_attempt"] = int(entry.get("previous_best_attempt", 0))
                entry.update(entry.get("previous_best_details", {}))
            else:
                entry["score"] = revised_score
                entry.update(stat_details)
            board[player_id] = entry
        self.campaign_results[stage_id] = {
            key: stats.get(key, default) for key, default in {
                "score": 0, "damage": 0, "property_damage": 0,
                "quests_done": 0, "quests_total": 0,
                "items_found": 0, "items_total": 0, "rescues": 0,
                "max_score": 1500,
            }.items()
        }
        self.campaign_results[stage_id].update({
            "choices": list(stats.get("choices", [])),
            "consequences": list(stats.get("consequences", [])),
            "resources": list(stats.get("resources", [])),
            "choice_points": int(stats.get("choice_points", 0)),
        })
        if stage_id == self.STAGE_ORDER[-1]:
            self.final_decision = str(stats.get("final_decision", self.final_decision))
        self.save()

    def stage_high_scores(self, stage_id):
        entries = self.high_scores.get(stage_id, {}).values()
        return sorted(entries, key=lambda entry: entry.get("score", 0), reverse=True)

    def campaign_summary(self):
        runs = list(self.campaign_results.values())
        if not runs:
            return {"points": 0, "score_rate": 0.0, "objective_rate": 0.0,
                    "item_rate": 0.0, "rescues": 0, "stages": 0, "stages_total": len(self.STAGE_ORDER)}
        points = sum(run.get("score", 0) for run in runs)
        max_points = sum(max(1, run.get("max_score", 1500)) for run in runs)
        done = sum(run.get("quests_done", 0) for run in runs)
        total = sum(run.get("quests_total", 0) for run in runs)
        items = sum(run.get("items_found", 0) for run in runs)
        item_total = sum(run.get("items_total", 0) for run in runs)
        return {
            "points": points,
            "score_rate": points / max_points if max_points else 0.0,
            "objective_rate": done / total if total else 0.0,
            "item_rate": items / item_total if item_total else 0.0,
            "rescues": sum(run.get("rescues", 0) for run in runs),
            "stages": len(runs),
            "stages_total": len(self.STAGE_ORDER),
            "damage": sum(run.get("damage", 0) for run in runs),
            "property_damage": sum(run.get("property_damage", 0) for run in runs),
            "evidence": sum(
                1 for run in runs for item in run.get("resources", [])
                if any(word in str(item).lower() for word in
                       ("component", "record", "map", "transmission", "key", "log"))
            ),
            "safe_decisions": sum(
                1 for run in runs for flag in run.get("choices", [])
                if str(flag).endswith("_safe") or flag in ("boarded", "stabilize")
            ),
            "risky_decisions": sum(
                1 for run in runs for flag in run.get("choices", [])
                if str(flag).endswith("_risk") or flag in
                   ("skipped", "rapid_shutdown", "abandon")
            ),
        }

    def campaign_ending(self):
        """Resolve the final story from all campaign points and outcomes."""
        summary = self.campaign_summary()
        if summary["stages"] == 0:
            return "bad"
        final_decision = getattr(self, "final_decision", "")
        if (summary["score_rate"] >= 0.76
                and summary["objective_rate"] >= 0.90
                and summary["item_rate"] >= 0.72
                and summary["property_damage"] <= 250
                and summary["rescues"] >= 2
                and summary["evidence"] >= 3
                and summary["safe_decisions"] >= 12
                and final_decision == "stabilize"):
            return "good"
        if (summary["score_rate"] >= 0.52
                and summary["objective_rate"] >= 0.65
                and summary["property_damage"] <= 650
                and final_decision != "abandon"):
            return "neutral"
        return "bad"

    def save(self):
        write_save({
            "version": 3,
            "campaign_version": 3,
            "character_id": self.character.get("id") if self.character else None,
            "challenger_id": self.challenger_id,
            "challenger_name": self.challenger_name,
            "unlocked": sorted(self.unlocked, key=self.STAGE_ORDER.index),
            "completed": sorted(self.completed, key=self.STAGE_ORDER.index),
            "records": self.records,
            "current_stage": self.current_stage,
            "difficulty": self.difficulty,
            "campaign_results": self.campaign_results,
            "final_decision": getattr(self, "final_decision", ""),
            "high_scores": self.high_scores,
        })

    def load(self, characters):
        data = load_save()
        if not data:
            return False
        by_id = {item["id"]: item for item in characters}
        self.character = by_id.get(data.get("character_id"))
        self.challenger_id = str(data.get("challenger_id", ""))[:14]
        self.challenger_name = str(data.get("challenger_name", self.challenger_id))[:14]
        migrated_campaign = int(data.get("campaign_version", 1)) < 3
        self.unlocked = {
            mapped for stage_id in data.get("unlocked", [])
            if (mapped := self.STAGE_ALIASES.get(stage_id, stage_id)) in self.STAGE_ORDER
        }
        self.completed = {
            mapped for stage_id in data.get("completed", [])
            if (mapped := self.STAGE_ALIASES.get(stage_id, stage_id)) in self.STAGE_ORDER
        }
        if migrated_campaign:
            # The supplied island route redefines mission order and score meaning.
            # Preserve player identity, but restart progression and stale mission scores.
            self.unlocked = {self.STAGE_ORDER[0]}
            self.completed = set()
        self.unlocked.add(self.STAGE_ORDER[0])
        records = data.get("records", {})
        self.records = records if isinstance(records, dict) else {}
        if migrated_campaign:
            self.records = {}
        high_scores = data.get("high_scores", {})
        self.high_scores = high_scores if isinstance(high_scores, dict) else {}
        if migrated_campaign:
            self.high_scores = {}
        migrated_scores = False
        for board in self.high_scores.values():
            if not isinstance(board, dict):
                continue
            for old_key, entry in list(board.items()):
                if not isinstance(entry, dict) or entry.get("player_id"):
                    continue
                hero_id = str(entry.get("character_id", old_key)).upper()
                player_id = f"PLAYER-{hero_id}"[:14]
                entry["player_id"] = player_id
                entry.setdefault("hero", entry.get("name", "Hero"))
                previous = board.get(player_id)
                if not previous or entry.get("score", 0) > previous.get("score", 0):
                    board[player_id] = entry
                if old_key != player_id:
                    board.pop(old_key, None)
                migrated_scores = True
        self.difficulty = data.get("difficulty", "standard")
        if self.difficulty not in ("relaxed", "standard", "challenge"):
            self.difficulty = "standard"
        self.campaign_results = data.get("campaign_results", {})
        self.final_decision = str(data.get("final_decision", ""))
        if not isinstance(self.campaign_results, dict):
            self.campaign_results = {}
        else:
            self.campaign_results = {
                stage_id: result for stage_id, result in self.campaign_results.items()
                if stage_id in self.STAGE_ORDER and isinstance(result, dict)
            }
        if migrated_campaign:
            self.campaign_results = {}
        stage = self.STAGE_ALIASES.get(data.get("current_stage"), data.get("current_stage"))
        self.current_stage = (self.STAGE_ORDER[0] if migrated_campaign
                              else stage if stage in self.unlocked else self.STAGE_ORDER[0])
        if self.character is None:
            return False
        if not self.challenger_id:
            self.challenger_id = f"PLAYER-{self.character['id'].upper()}"[:14]
            self.challenger_name = self.challenger_id
        if migrated_scores or not data.get("challenger_id") or migrated_campaign:
            self.save()  # migrate older campaign saves to the player-tag format
        return True

    def erase(self):
        self.reset()
        delete_save()
